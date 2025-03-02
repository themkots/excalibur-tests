import os
import reframe.core.launchers.mpi as rfmmpi


# OpenMPI Launcher on COSMA7 Rockport network:
# <https://www.dur.ac.uk/icc/cosma/support/rockport/>.
@rfmmpi.register_launcher('rockport_openmpi_mpirun')
class RockportOpenmpiLauncher(rfmmpi.MpirunLauncher):
    def command(self, job):
        return ['mpirun', '$RP_OPENMPI_ARGS']


# Some systems, notably some Cray-based ones, don't have access to the home filesystem.
# This means that if you set up Spack in your bashrc script, this file won't be loaded and
# the job will fail because it can't find `spack`.  This function allows propagating the
# setting of `PATH` on the node which submits the benchmark to script generated by ReFrame.
def spack_root_to_path():
    spack_root = os.getenv('SPACK_ROOT')
    path = os.getenv('PATH')
    if spack_root is None:
        return path
    else:
        spack_bindir = os.path.join(spack_root, 'bin')
        if path is None:
            return dir
        else:
            if spack_bindir in path.split(os.path.pathsep):
                return path
            else:
                return spack_bindir * os.path.pathsep * path


site_configuration = {
    'systems': [
        {
            # https://www.archer2.ac.uk/about/hardware.html
            # https://docs.archer2.ac.uk/
            'name': 'archer2',
            'descr': 'ARCHER2',
            'hostnames': ['ln[0-9]+'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'compute-node',
                    'descr': 'ARCHER2 compute nodes',
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    'env_vars': [
                        # Propagate PATH to compute nodes, including `spack` bindir
                        ['PATH', spack_root_to_path()],
                        # Work around for Spack erroring out on non-existing home directory:
                        # https://github.com/spack/spack/issues/33265#issuecomment-1277343920
                        ['SPACK_USER_CONFIG_PATH', os.path.expanduser("~").replace('home', 'work')],
                        ['SPACK_USER_CACHE_PATH',  os.path.expanduser("~").replace('home', 'work')],
                    ],
                    'access': ['--partition=standard'],
                    'environs': ['default'],
                    'max_jobs': 64,
                    'processor': {
                        'num_cpus': 128,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 64,
                    }
                },
            ]
        },  # end ARCHER2
        {
            # https://www.hpc.cam.ac.uk/index.php/high-performance-computing
            'name': 'csd3-rocky8',
            'descr': 'Cambridge Service for Data Driven Discovery - Rocky Linux 8 (RHEL8 compatible) nodes',
            'hostnames': ['login-q-[0-4]+'],
            'modules_system': 'tmod4',
            'partitions': [
                {
                    # https://docs.hpc.cam.ac.uk/hpc/user-guide/icelake.html
                    'name': 'icelake',
                    'descr': 'Ice Lake compute nodes',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'env_vars': [
                        ['I_MPI_PMI_LIBRARY', '/usr/local/software/slurm/current-rhel8/lib/libpmi2.so'],
                        ['I_MPI_OFI_PROVIDER', 'mlx'],
                        ['UCX_NET_DEVICES', 'mlx5_0:1'],
                    ],
                    'access': ['--partition=icelake', '--exclusive'],
                    'sched_options': {
                        'job_submit_timeout': 120,
                    },
                    'environs': ['default'],
                    'max_jobs': 64,
                    'processor': {
                        'num_cpus': 76,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 38,
                    },
                },
                {
                    'name': 'sapphirerapids',
                    'descr': 'Sapphire Rapids compute nodes',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'env_vars': [
                        ['I_MPI_PMI_LIBRARY', '/usr/local/software/slurm/current-rhel8/lib/libpmi2.so'],
                        ['I_MPI_OFI_PROVIDER', 'mlx'],
                        ['UCX_NET_DEVICES', 'mlx5_0:1'],
                    ],
                    'access': ['--partition=sapphire', '--exclusive'],
                    'sched_options': {
                        'job_submit_timeout': 120,
                    },
                    'environs': ['default'],
                    'max_jobs': 64,
                    'processor': {
                        'num_cpus': 112,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 56,
                    },
                },
            ]
        },  # end CSD3 Rocky 8
        {
            # https://www.hpc.cam.ac.uk/index.php/high-performance-computing
            'name': 'csd3-centos7',
            'descr': 'Cambridge Service for Data Driven Discovery - CentOS 7 (RHEL7 compatible) nodes',
            'hostnames': ['login-p-[0-4]+'],
            'modules_system': 'tmod32',
            'partitions': [
                {
                    # https://docs.hpc.cam.ac.uk/hpc/user-guide/cclake.html
                    'name': 'cascadelake',
                    'descr': 'Cascade Lake compute nodes',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'env_vars': [
                        ['I_MPI_PMI_LIBRARY', '/usr/local/software/slurm/current/lib/libpmi2.so'],
                        ['I_MPI_OFI_PROVIDER', 'mlx'],
                        ['UCX_NET_DEVICES', 'mlx5_0:1'],
                    ],
                    'access': ['--partition=cclake', '--exclusive'],
                    'sched_options': {
                        'job_submit_timeout': 120,
                    },
                    'environs': ['default'],
                    'max_jobs': 64,
                    'processor': {
                        'num_cpus': 56,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 28,
                    }
                },
            ]
        },  # end CSD3 CentOS 7
        {
            # https://www.rc.ucl.ac.uk/docs/Clusters/Myriad/#node-types
            'name': 'myriad',
            'descr': 'Myriad',
            'hostnames': ['login[0-9]+.myriad.ucl.ac.uk'],
            'partitions': [
                {
                    'name': 'cpu',
                    'descr': 'Computing nodes with CPUs only',
                    'scheduler': 'sge',
                    'launcher': 'mpirun',
                    'environs': ['default'],
                    'max_jobs': 36,
                    'processor': {
                        'num_cpus': 36,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 18,
                    },
                    'resources': [
                        {
                            'name': 'mpi',
                            'options': ['-pe mpi {num_slots}'],
                        },
                    ],
                },
                {
                    'name': 'a100',
                    'descr': 'Computing nodes with Nvidia A100 GPUs',
                    'scheduler': 'sge',
                    'access': ['-ac allow=L'],
                    'launcher': 'mpirun',
                    'environs': ['default'],
                    'max_jobs': 36,
                    'features': ['gpu', 'cuda'],
                    'processor': {
                        'num_cpus': 36,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 18,
                    },
                    'resources': [
                        {
                            'name': 'mpi',
                            'options': ['-pe mpi {num_slots}'],
                        },
                        {
                            'name': 'gpu',
                            'options': ['-l gpu={num_gpus_per_node}'],
                        },
                    ],
                },
                {
                    'name': 'p100',
                    'descr': 'Computing nodes with Nvidia P100 GPUs',
                    'scheduler': 'sge',
                    'access': ['-ac allow=J'],
                    'launcher': 'mpirun',
                    'environs': ['default'],
                    'max_jobs': 36,
                    'features': ['gpu', 'cuda'],
                    'processor': {
                        'num_cpus': 36,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 18,
                    },
                    'resources': [
                        {
                            'name': 'mpi',
                            'options': ['-pe mpi {num_slots}'],
                        },
                        {
                            'name': 'gpu',
                            'options': ['-l gpu={num_gpus_per_node}'],
                        },
                    ],
                },
                {
                    'name': 'v100',
                    'descr': 'Computing nodes with Nvidia V100 GPUs',
                    'scheduler': 'sge',
                    'access': ['-ac allow=EF'],
                    'launcher': 'mpirun',
                    'environs': ['default'],
                    'max_jobs': 36,
                    'features': ['gpu', 'cuda'],
                    'processor': {
                        'num_cpus': 36,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 18,
                    },
                    'resources': [
                        {
                            'name': 'mpi',
                            'options': ['-pe mpi {num_slots}'],
                        },
                        {
                            'name': 'gpu',
                            'options': ['-l gpu={num_gpus_per_node}'],
                        },
                    ],
                },
            ],
        },  # end Myriad
        {
            # https://gw4-isambard.github.io/docs/user-guide/MACS.html
            'name': 'isambard-macs',
            'descr': 'Isambard 2 - Multi-Architecture Comparison System',
            'hostnames': ['login-0[12].gw4.metoffice.gov.uk'],
            'partitions': [
                {
                    'name': 'cascadelake',
                    'descr': 'Intel Xeon Gold 6230 Cascade Lake computing nodes',
                    'scheduler': 'pbs',
                    'launcher': 'mpirun',
                    'access': ['-q clxq'],
                    'environs': ['default'],
                    'max_jobs': 20,
                    'processor': {
                        'num_cpus': 40,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 20,
                    },
                },
                {
                    'name': 'knl',
                    'descr': 'Intel Xeon Phi “Knights Landing” 7210 computing nodes',
                    'scheduler': 'pbs',
                    'launcher': 'mpirun',
                    'access': ['-q knlq'],
                    'environs': ['default'],
                    'max_jobs': 20,
                    'processor': {
                        'num_cpus': 64,
                        'num_cpus_per_core': 1,
                        'num_sockets': 1,
                        'num_cpus_per_socket': 64,
                    },
                },
                {
                    'name': 'rome',
                    'descr': 'AMD Epyc 7742 Rome computing nodes',
                    'scheduler': 'pbs',
                    'launcher': 'mpirun',
                    'access': ['-q romeq'],
                    'environs': ['default'],
                    'max_jobs': 20,
                    'processor': {
                        'num_cpus': 256,
                        'num_cpus_per_core': 2,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 64,
                    },
                },
                {
                    'name': 'pascal',
                    'descr': 'Broadwell computing nodes with Nvidia Pascal GPUs',
                    'scheduler': 'pbs',
                    'launcher': 'mpirun',
                    'access': ['-q pascalq'],
                    'environs': ['default'],
                    'max_jobs': 20,
                    'features': ['gpu', 'cuda'],
                    'processor': {
                        'num_cpus': 36,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 18,
                    },
                    'resources': [
                        {
                            'name': 'gpu',
                            'options': ['ngpus={num_gpus_per_node}'],
                        },
                    ],
                },
                {
                    'name': 'volta',
                    'descr': 'Cascadelake computing nodes with Nvidia Volta GPUs',
                    'scheduler': 'pbs',
                    'launcher': 'mpirun',
                    'access': ['-q voltaq'],
                    'environs': ['default'],
                    'max_jobs': 20,
                    'features': ['gpu', 'cuda'],
                    'processor': {
                        'num_cpus': 40,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 20,
                    },
                    'resources': [
                        {
                            'name': 'gpu',
                            'options': ['ngpus={num_gpus_per_node}'],
                        },
                    ],
                },
            ]
        },  # end Isambard MACS
        {
            # https://gw4-isambard.github.io/docs/user-guide/A64FX.html
            'name': 'isambard-a64fx',
            'descr': 'A64FX nodes of Isambard 2',
            'hostnames': ['gw4a64fxlogin[0-9]+'],
            'partitions': [
                {
                    'name': 'a64fx',
                    'descr': 'A64FX computing nodes',
                    'scheduler': 'pbs',
                    'launcher': 'mpirun',
                    'access': ['-q a64fx'],
                    'environs': ['default'],
                    'max_jobs': 20,
                    'processor': {
                        'num_cpus': 48,
                        'num_cpus_per_core': 1,
                        'num_sockets': 1,
                        'num_cpus_per_socket': 48,
                    },
                },
            ]
        },  # end Isambard A64FX
        {
            # https://gw4-isambard.github.io/docs/user-guide/PHASE3.html
            'name': 'isambard-phase3',
            'descr': 'Isambard 2 Phase 3 system',
            'hostnames': ['p3-login'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'ampere',
                    'descr': 'AMD Milan computing nodes with Nvidia Ampere GPUs',
                    'scheduler': 'pbs',
                    'launcher': 'mpirun',
                    'access': ['-q ampereq'],
                    'environs': ['default'],
                    'max_jobs': 20,
                    'features': ['gpu', 'cuda'],
                    'processor': {
                        'num_cpus': 64,
                        'num_cpus_per_core': 2,
                        'num_sockets': 1,
                        'num_cpus_per_socket': 32,
                    },
                    'resources': [
                        {
                            'name': 'gpu',
                             # TODO: memory should be a separate resource.
                            'options': ['ngpus={num_gpus_per_node}:mem=20G'],
                        },
                    ],
                },
                {
                    'name': 'instinct',
                    'descr': 'AMD Instinct GPU nodes with 4x AMD Instinct "MI100" GPU',
                    'scheduler': 'pbs',
                    'launcher': 'mpirun',
                    'access': ['-q instinctq', '-l place=excl'],
                    'environs': ['default'],
                    'max_jobs': 20,
                    'features': ['gpu', 'rocm'],
                    'processor': {
                        'num_cpus': 64,
                        'num_cpus_per_core': 2,
                        'num_sockets': 1,
                        'num_cpus_per_socket': 32,
                    }
                },
                {
                    'name': 'milan',
                    'descr': 'AMD EPYC 7713 64-Core Processor "Milan" compute nodes',
                    'scheduler': 'pbs',
                    'launcher': 'mpiexec',
                    'modules': ['cray-pals'],
                    'access': ['-q milanq'],
                    'environs': ['default'],
                    'max_jobs': 20,
                    'processor': {
                        'num_cpus': 256,
                        'num_cpus_per_core': 2,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 64,
                    },
                },
            ]
        },  # end Isambard Phase3
        {
            # https://gw4-isambard.github.io/docs/user-guide/XCI.html
            'name': 'isambard-xci',
            'descr': 'XCI - Marvell Thunder X2 nodes of Isambard 2',
            'hostnames': ['xcil0[0-1]'],
            'partitions': [
                {
                    'name': 'compute-node',
                    'descr': 'XCI computing nodes',
                    'scheduler': 'pbs',
                    'launcher': 'alps',
                    'access': ['-q arm'],
                    'environs': ['default'],
                    'max_jobs': 20,
                    'processor': {
                        'num_cpus': 256,
                        'num_cpus_per_core': 4,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 128,
                    },
                },
            ]
        },  # end Isambard XCI
        {
            'name': 'cosma7',
            'descr': 'COSMA',
            'hostnames': ['login7[a-z].pri.cosma[0-9].alces.network'],
            'modules_system': 'tmod4',
            'partitions': [
                # https://www.dur.ac.uk/icc/cosma/cosma7/
                {
                    'name': 'compute-node',
                    'descr': 'Compute nodes',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'access': ['--partition=cosma7'],
                    'environs': ['default'],
                    'max_jobs': 64,
                    'processor': {
                        'num_cpus': 28,
                        'num_cpus_per_core': 1,
                        'num_sockets': 1,
                        'num_cpus_per_socket': 28,
                    },
                },
                # https://www.dur.ac.uk/icc/cosma/support/rockport/
                {
                    'name': 'rockport-intelmpi-compute-node',
                    'descr': 'Rockport compute nodes using Intel MPI',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'modules': ['rockport-settings', 'ucx'],
                    'access': ['--partition=cosma7-rp'],
                    'environs': ['default'],
                    'max_jobs': 64,
                    'processor': {
                        'num_cpus': 28,
                        'num_cpus_per_core': 1,
                        'num_sockets': 1,
                        'num_cpus_per_socket': 28,
                    },
                },
                # https://www.dur.ac.uk/icc/cosma/support/rockport/
                {
                    'name': 'rockport-openmpi-compute-node',
                    'descr': 'Rockport compute nodes using OpenMPI',
                    'scheduler': 'slurm',
                    'launcher': 'rockport_openmpi_mpirun',
                    'modules': ['rockport-settings', 'ucx'],
                    'access': ['--partition=cosma7-rp'],
                    'environs': ['default'],
                    'max_jobs': 64,
                    'processor': {
                        'num_cpus': 28,
                        'num_cpus_per_core': 1,
                        'num_sockets': 1,
                        'num_cpus_per_socket': 28,
                    },
                },
            ]
        },  # end cosma7
        {
            # https://www.dur.ac.uk/icc/cosma/support/cosma8/
            'name': 'cosma8',
            'descr': 'COSMA',
            'hostnames': ['login8[a-z].pri.cosma[0-9].alces.network'],
            'modules_system': 'tmod4',
            'partitions': [
                {
                    'name': 'compute-node',
                    'descr': 'Compute nodes',
                    'scheduler': 'slurm',
                    'launcher': 'mpiexec',
                    'access': ['--partition=cosma8'],
                    'environs': ['default', 'intel20-mpi-durham', 'intel20_u2-mpi-durham', 'intel19-mpi-durham', 'intel19_u3-mpi-durham'],
                    'sched_options': {
                        'use_nodes_option': True,
                    },
                    'max_jobs': 64,
                    'processor': {
                        'num_cpus': 128,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 64,
                    },
                }
            ]
        },  # end cosma8
        {
            'name': 'github-actions',
            'descr': 'GitHub Actions runner',
            'hostnames': ['fv-az.*'],  # Just to not have '.*'
            'max_local_jobs': 1,  # Limit number of parallel jobs
            'partitions': [
                {
                    'name': 'default',
                    'scheduler': 'local',
                    'launcher': 'mpirun',
                    'environs': ['default']
                }
            ]
        },  # End GitHub Actions
        {
            # https://epcced.github.io/dirac-docs/tursa-user-guide/scheduler/#partitions
            'name': 'tursa',
            'descr': 'Tursa',
            'hostnames': ['tursa-login.*'],
            'partitions': [
                {
                    'name': 'gpu',
                    'descr': 'GPU computing nodes',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'access': ['--partition=gpu', '--qos=standard'],
                    'environs': ['default'],
                    'features': ['gpu', 'cuda'],
                    'sched_options': {
                        'use_nodes_option': True,
                    },
                    'max_jobs': 16,
                    'processor': {
                        'num_cpus': 64,
                        'num_cpus_per_core': 2,
                        'num_sockets': 1,
                        'num_cpus_per_socket': 32,
                    },
                    'resources': [
                        {
                            'name': 'gpu',
                            'options': ['--gres=gpu:{num_gpus_per_node}']
                        },
                    ],
                },
            ]
        },  # end Tursa
        {
            # https://dial3-docs.dirac.ac.uk/DIaL2.5/Architecture/
            'name': 'dial2',
            'descr': 'Dirac Data Intensive @ Leicester',
            'hostnames': ['dirac0*'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'compute-node',
                    'descr': 'Computing nodes',
                    'scheduler': 'torque',
                    'launcher': 'mpirun',
                    'environs': ['default'],
                    'max_jobs': 64,
                    'processor': {
                        'num_cpus': 36,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 18,
                    },
                },
            ]
        },  # end DiaL2
        {
            # https://dial3-docs.dirac.ac.uk/About_dial3/architecture/
            'name': 'dial3',
            'descr': 'Dirac Data Intensive @ Leicester',
            'hostnames': ['d3-login.*'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'compute-node',
                    'descr': 'Computing nodes',
                    'scheduler': 'slurm',
                    'launcher': 'mpirun',
                    'environs': ['default', 'intel-oneapi-openmpi-dial3','intel19-mpi-dial3'],
                    'max_jobs': 64,
                    'processor': {
                        'num_cpus': 128,
                        'num_cpus_per_core': 1,
                        'num_sockets': 2,
                        'num_cpus_per_socket': 64,
                    },
                },
            ]
        },  # end DiaL3
        {
            'name': 'default',
            'descr': 'Default system',
            'hostnames': ['.*'],
            'partitions': [
                {
                    'name': 'default',
                    'scheduler': 'local',
                    'launcher': 'mpirun',
                    'environs': ['default'],
                },
            ]
        },  # end default
        # < insert new systems here >
    ],
    'environments': [
        {
            # Since we always build with spack, we are not using the compilers in this environment.
            # The compilers spack uses are definied in the spack specs of the reframe config
            # for each app. Nevertheless, we have to define an environment here to make ReFrame happy.
            'name': 'default',
            'cc': 'cc',
            'cxx': 'c++',
            'ftn': 'ftn'
        },
        {
            'name': 'intel20-mpi-durham',
            'modules':['intel_comp/2020','intel_mpi/2020'],
            'cc': 'mpiicc',
            'cxx': 'mpiicpc',
            'ftn': 'mpiifort'
        },
        {
            'name': 'intel20_u2-mpi-durham',
            'modules':['intel_comp/2020-update2','intel_mpi/2020-update2'],
            'cc': 'mpiicc',
            'cxx': 'mpiicpc',
            'ftn': 'mpiifort'
        },
        {
            'name': 'intel19-mpi-durham',
            'modules':['intel_comp/2019','intel_mpi/2019'],
            'cc': 'mpiicc',
            'cxx': 'mpiicpc',
            'ftn': 'mpiifort'
        },
        {
            'name': 'intel19_u3-mpi-durham',
            'modules':['intel_comp/2019-update3','intel_mpi/2019-update3'],
            'cc': 'mpiicc',
            'cxx': 'mpiicpc',
            'ftn': 'mpiifort'
        },
        {
            'name':'intel-oneapi-openmpi-dial3',
            'modules':['intel-oneapi-compilers/2021.2.0','openmpi4/intel/4.0.5'],
            'cc':'mpicc',
            'cxx':'mpicxx',
            'ftn':'mpif90'
        },
        {
            'name': 'intel19-mpi-dial3',
            'modules':['intel-parallel-studio/cluster.2019.5'],
            'cc': 'mpiicc',
            'cxx': 'mpiicpc',
            'ftn': 'mpiifort'
        },
    ],
    'logging': [
        {
            'level': 'debug',
            'handlers': [
                {
                    'type': 'stream',
                    'name': 'stdout',
                    'level': 'info',
                    'format': '%(message)s'
                },
                {
                    'type': 'file',
                    'level': 'debug',
                    'format': '[%(asctime)s] %(levelname)s: %(check_info)s: %(message)s',   # noqa: E501
                    'append': False
                }
            ],
            'handlers_perflog': [
                {
                    'type': 'filelog',
                    'prefix': '%(check_system)s/%(check_partition)s',
                    'level': 'info',
                    'format': (
                        '%(check_job_completion_time)s|'
                        'reframe %(version)s|'
                        '%(check_info)s|'
                        '%(check_jobid)s|'
                        '%(check_num_tasks)s|'
                        '%(check_num_cpus_per_task)s|'
                        '%(check_num_tasks_per_node)s|'
                        '%(check_num_gpus_per_node)s|'
                        '%(check_perfvalues)s|'
                        '%(check_spack_spec)s|'
                        '%(check_display_name)s|'
                        '%(check_system)s|'
                        '%(check_partition)s|'
                        '%(check_environ)s|'
                        '%(check_extra_resources)s|'
                        '%(check_env_vars)s|'
                        '%(check_tags)s'
                    ),
                    'format_perfvars': (
                        '%(check_perf_value)s|'
                        '%(check_perf_unit)s|'
                        '%(check_perf_ref)s|'
                        '%(check_perf_lower_thres)s|'
                        '%(check_perf_upper_thres)s|'
                    ),
                    'append': True
                }
            ]
        }
    ],
}
