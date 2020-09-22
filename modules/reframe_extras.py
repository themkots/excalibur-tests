""" Extra functionality for reframe

"""

import reframe as rfm
from reframe.core.buildsystems import BuildSystem
from reframe.core.logging import getlogger
from reframe.core.launchers import JobLauncher
import reframe.utility.sanity as sn

import os, shutil, subprocess, shlex, subprocess
from pprint import pprint

class CachedRunTest(rfm.RegressionTest):
    """ Mixin. TODO: document properly.

        Classes using this can be derive from `rfm.RunOnlyRegressionTest`
        Assumes saved output files are in a directory `cache/` in same parent directory (and with same directory tree) as the `output/` and `stage/` directories.

        set self.use_cache to True or a path relative to cwd.
    
        NB Any class using this MUST NOT change self.executable in a method decorated with `@rfm.run_before('run')` as that will override functionality here.
    """

    @rfm.run_before('run')
    def no_run(self):
        """ Turn the run phase into a no-op. """

        if self.use_cache:
            with open(os.path.join(self.stagedir, 'noop.sh'), 'w') as noop:
                noop.write('#!/bin/bash\necho "noop $@"\n')
            self.executable = "./noop.sh"

    @rfm.run_after('run')
    def copy_saved_output(self):
        """ Copy saved output files to stage dir. """

        if self.use_cache:
            # find the part of the path common to both output and staging:
            rtc = rfm.core.runtime.runtime()
            tree_path = os.path.relpath(self.outputdir, rtc.output_prefix)
            
            cache_root = 'cache' if self.use_cache == True else self.use_cache

            saved_output_dir = os.path.join(cache_root, tree_path)
            
            if not os.path.exists(saved_output_dir) or not os.path.isdir(saved_output_dir):
                raise ValueError("cached output directory %s does not exist or isn't a directory" % os.path.abspath(saved_output_dir))

            import distutils.dir_util
            distutils.dir_util.copy_tree(saved_output_dir, self.stagedir)


class CachedCompileOnlyTest(rfm.CompileOnlyRegressionTest):
    """ A compile-only test with caching of binaries between `reframe` runs.
    
        Test classes derived from this class will save `self.executable` to a ./builds/{system}/{partition}/{environment}/{self.name}` directory after compilation.
        However if this path (including the filename) exists before compilation (i.e. on the next run):
            - No compilation occurs
            - `self.sourcesdir` is set to this directory, so `reframe` will copy the binary to the staging dir (as if compilation had occured)
            - A new attribute `self.build_path` is set to this path (otherwise None)

        Note that `self.sourcesdir` is only manipulated if no compilation occurs, so compilation test-cases which modify this to specify the source directory should be fine.

        TODO: Make logging tidier - currently produces info-level (stdout by default) messaging on whether cache is used.
    """
    @rfm.run_before('compile')
    def conditional_compile(self):
        build_dir = os.path.abspath(os.path.join('builds', self.current_system.name, self.current_partition.name, self.current_environ.name, self.name))
        build_path = os.path.join(build_dir, self.executable)
        if os.path.exists(build_path):
            self.build_path = build_path
            getlogger().info('found exe at %r', self.build_path)
            self.build_system = NoBuild()
            self.sourcesdir = build_dir # means reframe will copy the exe back in
        else:
            self.build_path = None

    @rfm.run_after('compile')
    def copy_executable(self):
        if not self.build_path: # i.e. only if actually did a compile:
            self.exes_dir = os.path.join('builds', self.current_system.name, self.current_partition.name, self.current_environ.name, self.name)
            exe_path = os.path.join(self.stagedir, self.executable)
            build_path = os.path.join(self.exes_dir, self.executable)
            build_dir = os.path.dirpath(build_path) # self.executable might include a directory
            if not os.path.exists(build_dir):
                os.makedirs(build_dir)
            shutil.copy(exe_path, build_path)
            getlogger().info('copied exe to %r', build_path)

class NoBuild(BuildSystem):
    """ A no-op build system """
    def __init__(self):
        super().__init__()
    def emit_build_commands(self, environ):
        return []

def slurm_node_info(partition=None):
    """ Get information about slurm nodes.

        Args:
            partition: str, name of slurm partition to query, else information for all partitions is returned.

        Returns a sequence of dicts, one per node with keys/values all strs as follows:
            "NODELIST": name of node
            "NODES": number of nodes
            "PARTITION": name of partition, * appended if default
            "STATE": e.g. "idle"
            "CPUS": str number of cpus
            "S:C:T": Extended processor information: number of sockets, cores, threads in format "S:C:T"
            "MEMORY": Size of memory in megabytes
            "TMP_DISK": Size of temporary disk space in megabytes
            "WEIGHT": Scheduling weight of the node
            "AVAIL_FE": ?
            "REASON": The reason a node is unavailable (down, drained, or draining states) or "none"
        See `man sinfo` for `sinfo --Node --long` for full details.

        TODO: add partition selection? with None being current one (note system partition != slurm partition)
    """
    sinfo_cmd = ['sinfo', '--Node', '--long']
    if partition:
        sinfo_cmd.append('--partition=%s' % partition)
    nodeinfo = subprocess.run(sinfo_cmd, capture_output=True).stdout.decode('utf-8') # encoding?

    nodes = []
    lines = nodeinfo.split('\n')
    header = lines[1].split() # line[0] is date/time
    for line in lines[2:]:
        line = line.split()
        if not line:
            continue
        nodes.append({})
        for ci, key in enumerate(header):
            nodes[-1][key] = line[ci]
    return nodes


def hostlist_to_hostnames(s):
    """ Convert a Slurm 'hostlist expression' to a list of individual node names.
    
        Uses `scontrol` command.
    """
    hostnames = subprocess.run(['scontrol', 'show', 'hostnames', s], capture_output=True, text=True).stdout.split()
    return hostnames

class Scheduler_Info(object):
    def __init__(self, rfm_partition=None, exclude_states=None, only_states=None):
        """ Information from the scheduler.

            Args:
                rfm_partition: reframe.core.systems.SystemPartition or None
                exclude_states: sequence of str, exclude nodes in these Slurm node states
                only_states: sequence of str, only include nodes in these Slurm node states
            
            The returned object has attributes:
                - `num_nodes`: number of nodes
                - `pcores_per_node`: number of physical cores per node
                - `lcores_per_node`: number of logical cores per node
            
            If `rfm_partition` is None the above attributes describe the **default** scheduler partition. Otherwise the following `sbatch` directives
            in the `access` property of the ReFrame partition will affect the information returned:
                - `--partition`
                - `--exclude`
        """
        # TODO: handle scheduler not being slurm!
        slurm_partition_name = None
        slurm_excluded_nodes = []
        exclude_states = [] if exclude_states is None else exclude_states
        only_states = [] if only_states is None else only_states
        if rfm_partition is not None:
            for option in rfm_partition.access:
                if '--partition=' in option:
                    _, slurm_partition_name = option.split('=')
                if '--exclude' in option:
                    _, exclude_hostlist = option.split('=')
                    slurm_excluded_nodes = hostlist_to_hostnames(exclude_hostlist)
        
        # filter out nodes we don't want:
        nodeinfo = []
        for node in slurm_node_info(slurm_partition_name):
            if slurm_partition_name is None and not node['PARTITION'].endswith('*'): # filter to default partition
                continue
            if node['NODELIST'] in slurm_excluded_nodes:
                continue
            if node['STATE'].strip('*') in exclude_states:
                continue
            if only_states and node['STATE'] not in only_states:
                continue
            nodeinfo.append(node)
            
        self.num_nodes = len(nodeinfo)
        cpus = [n['S:C:T'] for n in nodeinfo]
        if not len(set(cpus)) == 1:
            raise ValueError('Cannot summarise CPUs - description differs between nodes:\n%r' % cpus)
        sockets, cores, threads = [int(v) for v in cpus[0].split(':')] # nb each is 'per' the preceeding
        self.sockets_per_node = sockets
        self.pcores_per_node = sockets * cores
        self.lcores_per_node = sockets * cores * threads

    def __str__(self):

        descr = ['%s=%s' % (k, getattr(self, k)) for k in ['num_nodes', 'sockets_per_node', 'pcores_per_node', 'lcores_per_node']]

        return 'Scheduler_Info(%s)' % (', '.join(descr))

def sequence(start, end, factor):
    """ Like `range()` but each term is `factor` * previous term.

        `start` is inclusive, `end` is exclusive.

        Returns a list.
    """

    values = []
    v = start
    while v < end:
        values.append(v)
        v *= factor
    return values

if __name__ == '__main__':
    import sys
    # will need something like:
    # [hpc-tests]$ PYTHONPATH='reframe' python modules/reframe_extras.py
    if len(sys.argv) == 1:
        print(Scheduler_Info())
    else:
        print(Scheduler_Info(sys.argv[1]))
    