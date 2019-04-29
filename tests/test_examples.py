# LAMMPS regression test driver using Python's unittest
#
# Run with "nosetests -v" in main LAMMPS folder
# Run with "nosetests  --with-xunit" to generate xUnit report file
__author__ = 'Richard Berger'
__email__ = "richard.berger@temple.edu"

import unittest
import os
import glob
from lammps_testing.testrunner import LAMMPSTestCase, SkipTest, LAMMPS_DIR, LAMMPS_MPI_MODE, LAMMPS_TEST_MODES

TESTS_DIR=os.path.dirname(os.path.realpath(__file__))

def CreateLAMMPSTestCase(testcase_name, script_names):
    """ Utility function to generate LAMMPS test case classes with both serial and parallel
        testing functions for each input script"""
    def setUp(self):
        self.cwd = os.path.join(TESTS_DIR, "examples", testcase_name)

    def test_serial(func_name, script_name):
        def test_serial_run(self):
            rc = self.run_script(script_name)
            self.assertEqual(rc, 0)
        test_serial_run.__name__ = func_name
        return test_serial_run

    def test_parallel(func_name, script_name):
        def test_parallel_run(self):
            rc = self.run_script(script_name, nprocs=4)
            self.assertEqual(rc, 0)
        test_parallel_run.__name__ = func_name
        return test_parallel_run

    def test_gpu(func_name, script_name):
        def test_gpu_run(self):
            rc = self.run_script(script_name, force_gpu=True)
            self.assertEqual(rc, 0)
        test_gpu_run.__name__ = func_name
        return test_gpu_run

    def test_kokkos_omp(func_name, script_name):
        def test_kokkos_omp_run(self):
            rc = self.run_script(script_name, force_kokkos=True, nthreads=4)
            self.assertEqual(rc, 0)
        test_kokkos_omp_run.__name__ = func_name
        return test_kokkos_omp_run

    def test_kokkos_cuda(func_name, script_name):
        def test_kokkos_cuda_run(self):
            rc = self.run_script(script_name, force_kokkos=True, force_cuda=True)
            self.assertEqual(rc, 0)
        test_kokkos_cuda_run.__name__ = func_name
        return test_kokkos_cuda_run

    def test_kokkos_cuda_omp(func_name, script_name):
        def test_kokkos_cuda_omp_run(self):
            rc = self.run_script(script_name, force_kokkos=True, force_cuda=True, nthreads=4)
            self.assertEqual(rc, 0)
        test_kokkos_cuda_omp_run.__name__ = func_name
        return test_kokkos_cuda_omp_run

    def test_parallel_omp(func_name, script_name):
        def test_parallel_omp_run(self):
            rc = self.run_script(script_name, nthreads=4, force_openmp=True)
            self.assertEqual(rc, 0)
        test_parallel_omp_run.__name__ = func_name
        return test_parallel_omp_run

    def test_serial_valgrind(func_name, name, script_name):
        valgrind_exec = ["valgrind", "--leak-check=full", "--xml=yes", "--xml-file=" + name + ".memcheck"]

        if LAMMPS_MPI_MODE == "openmpi" and os.path.exists("/usr/share/openmpi/openmpi-valgrind.supp"):
            valgrind_exec += ["--suppressions=/usr/share/openmpi/openmpi-valgrind.supp"]

        def test_serial_valgrind_run(self):
            rc = self.run_script(script_name,launcher=valgrind_exec)
            self.assertEqual(rc, 0)
        test_serial_valgrind_run.__name__ = func_name
        return test_serial_valgrind_run

    methods = {"setUp": setUp}

    for script_name in script_names:
        name = '_'.join(script_name.split('.')[1:])

        if 'serial' in LAMMPS_TEST_MODES:
            func_name = "test_" + name + "_serial"
            methods[func_name] = test_serial(func_name, script_name)

        if 'gpu' in LAMMPS_TEST_MODES:
            func_name = "test_" + name + "_gpu"
            methods[func_name] = test_gpu(func_name, script_name)

        if 'kokkos_omp' in LAMMPS_TEST_MODES:
            func_name = "test_" + name + "_kokkos_omp"
            methods[func_name] = test_kokkos_omp(func_name, script_name)

        if 'kokkos_cuda' in LAMMPS_TEST_MODES:
            func_name = "test_" + name + "_kokkos_cuda"
            methods[func_name] = test_kokkos_cuda(func_name, script_name)

        if 'kokkos_cuda_omp' in LAMMPS_TEST_MODES:
            func_name = "test_" + name + "_kokkos_cuda_omp"
            methods[func_name] = test_kokkos_cuda_omp(func_name, script_name)

        if 'parallel' in LAMMPS_TEST_MODES:
            func_name = "test_" + name + "_parallel"
            methods[func_name] = test_parallel(func_name, script_name)

        if 'omp' in LAMMPS_TEST_MODES:
            func_name = "test_" + name + "_parallel_omp"
            methods[func_name] = test_parallel_omp(func_name, script_name)

        if 'valgrind' in LAMMPS_TEST_MODES:
            func_name = "test_" + name + "_serial_valgrind"
            methods[func_name] = test_serial_valgrind(func_name, name, script_name)

    return type(testcase_name.title() + "TestCase", (LAMMPSTestCase, unittest.TestCase), methods)


# collect all the script files and generate the tests automatically by a recursive search and
# skipping a selection of folders

examples_dir = os.path.join(TESTS_DIR, 'examples')

skip_list = ['accelerate', 'kim', 'neb', 'reax', 'rerun', 'tad', 'prd', 'mscg']

for name in os.listdir(examples_dir):
    path = os.path.join(examples_dir, name)

    if name in skip_list:
        continue

    # for now only use the lower case examples (=simple ones)

    if name.islower() and os.path.isdir(path):
        script_names = map(os.path.basename, glob.glob(os.path.join(path, 'in.*')))
        vars()[name.title() + "TestCase"] = CreateLAMMPSTestCase(name, script_names)

if 'omp' in LAMMPS_TEST_MODES:
    SkipTest(CombTestCase, "test_comb3_parallel_omp", "comb3 currently not supported by USER-OMP")
    SkipTest(SnapTestCase, "test_snap_hybrid_WSNAP_HePair_parallel_omp", "snap_hybrid currently not supported by USER-OMP")
    SkipTest(HugoniostatTestCase, "test_hugoniostat_parallel_omp", "Broken with USER-OMP")

if 'parallel' in LAMMPS_TEST_MODES:
    SkipTest(BalanceTestCase, "test_balance_bond_fast_parallel", "Crashes randomly")

if 'gpu' in LAMMPS_TEST_MODES:
    SkipTest(CombTestCase, "test_comb3_gpu", "requires newton pair on")
    SkipTest(CombTestCase, "test_comb_Cu2O_elastic_gpu", "requires newton pair on")
    SkipTest(CombTestCase, "test_comb_Cu_gpu", "requires newton pair on")
    SkipTest(CombTestCase, "test_comb_HfO2_gpu", "requires newton pair on")
    SkipTest(CombTestCase, "test_comb_Si_elastic_gpu", "requires newton pair on")
    SkipTest(CombTestCase, "test_comb_Si_gpu", "requires newton pair on")

    SkipTest(CrackTestCase, "test_crack_gpu", "Cannot use neigh_modify exclude with GPU neighbor builds")

    SkipTest(DreidingTestCase, "test_dreiding_gpu", "requires newton pair on")

    SkipTest(EllipseTestCase, "test_ellipse_gayberne_gpu", "CPU neighbor lists must be used for ellipsoid/sphere mix")

    SkipTest(GcmcTestCase, "test_gcmc_co2_gpu", "Cannot use neigh_modify exclude with GPU neighbor builds")
    SkipTest(GcmcTestCase, "test_gcmc_h2o_gpu", "Cannot use neigh_modify exclude with GPU neighbor builds")
    SkipTest(GcmcTestCase, "test_gcmc_lj_gpu", "Cannot use neigh_modify exclude with GPU neighbor builds")

    SkipTest(GranregionTestCase, "test_granregion_box_gpu", "Cannot use pair hybrid with GPU neighbor list builds")

    SkipTest(MeamTestCase, "test_meam_gpu", "requires newton pair on")
    SkipTest(MeamTestCase, "test_meam_shear_gpu", "requires newton pair on")

    SkipTest(Nb3BTestCase, "test_nb3b_gpu", "requires newton pair on")

    SkipTest(NemdTestCase, "test_nemd_gpu", "Cannot use package gpu neigh yes with triclinic box")

    SkipTest(PythonTestCase, "test_pair_python_hybrid_gpu", "Cannot use pair hybrid with GPU neighbor list builds")
    SkipTest(PythonTestCase, "test_pair_python_long_gpu", "Cannot use pair hybrid with GPU neighbor list builds")
    SkipTest(PythonTestCase, "test_pair_python_spce_gpu", "Cannot use pair hybrid with GPU neighbor list builds")

    SkipTest(QeqTestCase, "test_qeq_buck_gpu", "QEQ with 'newton pair off' not supported")
    SkipTest(QeqTestCase, "test_qeq_reaxc_gpu", "requires newton pair on")

    SkipTest(RigidTestCase, "test_rigid_gpu", "Cannot use neigh_modify exclude with GPU neighbor builds")
    SkipTest(RigidTestCase, "test_rigid_poems2_gpu", "Cannot use neigh_modify exclude with GPU neighbor builds")
    SkipTest(RigidTestCase, "test_rigid_poems_gpu", "Cannot use neigh_modify exclude with GPU neighbor builds")
    SkipTest(RigidTestCase, "test_rigid_tnr_gpu", "Cannot use neigh_modify exclude with GPU neighbor builds")

    SkipTest(SnapTestCase, "test_snap_gpu", "requires newton pair on")
    SkipTest(SnapTestCase, "test_snap_hybrid_WSNAP_HePair_gpu", "requires newton pair on")
    SkipTest(SnapTestCase, "test_snap_Ta06A_gpu", "requires newton pair on")
    SkipTest(SnapTestCase, "test_snap_W_2940_gpu", "requires newton pair on")

    SkipTest(VashishtaTestCase, "test_vashishta_sio2_gpu", "Cannot use package gpu neigh yes with triclinic box")
    SkipTest(VashishtaTestCase, "test_vashishta_table_inp_gpu", "Cannot use package gpu neigh yes with triclinic box")
    SkipTest(VashishtaTestCase, "test_vashishta_table_sio2_gpu", "Cannot use package gpu neigh yes with triclinic box")
    SkipTest(VashishtaTestCase, "test_vashishta_inp_gpu", "Cannot use package gpu neigh yes with triclinic box")

    SkipTest(SrdTestCase, "test_srd_mixture_gpu", "requires newton pair on")
    SkipTest(SrdTestCase, "test_srd_pure_gpu", "requires newton pair on")

    SkipTest(StreitzTestCase, "test_streitz_ewald_gpu", "Cannot use pair hybrid with GPU neighbor list builds")
    SkipTest(StreitzTestCase, "test_streitz_wolf_gpu", "Cannot use pair hybrid with GPU neighbor list builds")

    SkipTest(VoronoiTestCase, "test_voronoi_gpu", "Cannot use package gpu neigh yes with triclinic box")

if __name__ == '__main__':
    unittest.main()
