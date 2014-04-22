import lockfile.linklockfile
import lockfile.mkdirlockfile
import lockfile.pidlockfile
import lockfile.symlinklockfile

from compliancetest import NonThreadDistinguishingTest, ThreadDistinguishingTest


class TestLinkLockFile(NonThreadDistinguishingTest):
    class_to_test = lockfile.linklockfile.LinkLockFile
class TestLinkLockFileThreaded(ThreadDistinguishingTest):
    class_to_test = lockfile.linklockfile.LinkLockFile


class TestSymlinkLockFile(NonThreadDistinguishingTest):
    class_to_test = lockfile.symlinklockfile.SymlinkLockFile
class TestSymlinkLockFileThreaded(ThreadDistinguishingTest):
    class_to_test = lockfile.symlinklockfile.SymlinkLockFile


class TestMkdirLockFile(NonThreadDistinguishingTest):
    class_to_test = lockfile.mkdirlockfile.MkdirLockFile
class TestMkdirLockFileThreaded(ThreadDistinguishingTest):
    class_to_test = lockfile.mkdirlockfile.MkdirLockFile


class TestPIDLockFile(NonThreadDistinguishingTest):
    class_to_test = lockfile.pidlockfile.PIDLockFile
# PIDLockFile class does not currently support distinguishing between threads.
# Could be possible if both the pid and thread id was written to the PID file.
#class TestPIDLockFileThreaded(ThreadDistinguishingTest):
#    class_to_test = lockfile.pidlockfile.PIDLockFile


# Check backwards compatibility
class TestLinkFileLock(NonThreadDistinguishingTest):
    class_to_test = lockfile.LinkFileLock
class TestLinkFileLockThreaded(ThreadDistinguishingTest):
    class_to_test = lockfile.LinkFileLock


class TestMkdirFileLock(NonThreadDistinguishingTest):
    class_to_test = lockfile.MkdirFileLock
class TestMkdirFileLockThreaded(ThreadDistinguishingTest):
    class_to_test = lockfile.MkdirFileLock


try:
    import sqlite3
except ImportError:
    pass
else:
    import lockfile.sqlitelockfile
    class TestSQLiteLockFile(NonThreadDistinguishingTest):
        class_to_test = lockfile.sqlitelockfile.SQLiteLockFile
# TODO: Seems that the SQLiteLockFile class should handle distinguishing
# between threads, but these tests currently failing.
#    class TestSQLiteLockFileThreaded(ThreadDistinguishingTest):
#        class_to_test = lockfile.sqlitelockfile.SQLiteLockFile
