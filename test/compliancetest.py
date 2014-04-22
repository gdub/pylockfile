from functools import wraps
import os
import threading
import shutil

import lockfile


def acquire_lock_in_first_thread(func):
    """
    Decorator for use on ComplianceTest class/subclasses methods to factor
    out broiler plate code of grabbing a lock with one thread and creating
    a second lock to pass as an arument to the decorated test method.
    """
    @wraps(func)
    def wrapper(self, *args, **kwds):
        e1, e2 = threading.Event(), threading.Event()
        t = _in_thread(self._lock_wait_unlock, e1, e2, self.threaded)
        e1.wait()                # wait for thread t to acquire lock
        lock2 = self.class_to_test(self.test_file, threaded=self.threaded)
        assert lock2.is_locked()

        return func(self, lock2, *args, **kwds)

        e2.set()
        t.join()
    return wrapper


class ComplianceTest(object):

    threaded = None

    def _lock_wait_unlock(self, event1, event2, tbool):
        """Lock from another thread.  Helper for tests."""
        l = self.class_to_test(self.test_file, threaded=tbool)
        l.acquire()
        try:
            event1.set()  # we're in,
            event2.wait() # wait for boss's permission to leave
        finally:
            l.release()

    def setup(self):
        """
        Make a temporary directory for placing files in and calculate a test
        file path to pass when creating LockFile objects.
        """
        import tempfile
        self.test_dir = os.path.join(tempfile.gettempdir(),
                                     'trash-%s' % os.getpid())
        os.makedirs(self.test_dir)
        self.test_file = os.path.join(self.test_dir, 'testfile-%s' % os.getpid())

    def teardown(self):
        shutil.rmtree(self.test_dir)

    def _assert_already_locked(self, lock, timeout):
        try:
            lock.acquire(timeout=timeout)
        except lockfile.AlreadyLocked:
            pass
        else:
            lock.release()
            raise AssertionError("did not raise AlreadyLocked in"
                                 " thread %s" %
                                 threading.current_thread().get_name())

    def _assert_lock_timeout(self, lock, timeout):
        try:
            lock.acquire(timeout=timeout)
        except lockfile.LockTimeout:
            pass
        else:
            lock.release()
            raise AssertionError("did not raise LockTimeout in thread %s" %
                                 threading.current_thread().get_name())

    def _assert_lock_acquired(self, lock, timeout):
        lock.acquire(timeout=timeout)
        assert lock.is_locked()
        assert lock.i_am_locking()

    def test_single_lock_acquire(self):
        lock = self.class_to_test(self.test_file, threaded=self.threaded)
        assert not lock.is_locked()
        assert not lock.i_am_locking()
        lock.acquire()
        assert lock.is_locked()
        assert lock.i_am_locking()
        lock.release()
        assert not lock.is_locked()
        assert not lock.i_am_locking()

    def test_multiple_release(self):
        lock = self.class_to_test(self.test_file, threaded=self.threaded)
        lock.acquire()
        lock.release()
        assert not lock.is_locked()
        assert not lock.i_am_locking()
        try:
            lock.release()
        except lockfile.NotLocked:
            pass
        except lockfile.NotMyLock:
            raise AssertionError('unexpected exception: %s' %
                                 lockfile.NotMyLock)
        else:
            raise AssertionError('erroneously unlocked file')

    def test_break_lock(self):
        lock = self.class_to_test(self.test_file, threaded=self.threaded)
        lock.acquire()
        assert lock.is_locked()
        lock2 = self.class_to_test(self.test_file, threaded=self.threaded)
        assert lock2.is_locked()
        lock2.break_lock()
        assert not lock.is_locked()
        assert not lock2.is_locked()
        try:
            lock.release()
        except lockfile.NotLocked:
            pass
        else:
            raise AssertionError('break lock failed')

    def test_decorator(self):
        @lockfile.locked(self.test_file)
        def func(a, b):
            return a + b
        assert func(4, 3) == 7

    def test_context_manager(self):
        with lockfile.LockFile(self.test_file) as lock:
            assert lock.is_locked()
            assert lock.i_am_locking()
        assert not lock.is_locked()
        assert not lock.i_am_locking()


class NonThreadDistinguishingTest(ComplianceTest):
    """
    Assertion tests for Lockfile objects that DO NOT distinguish between
    threads in the same process.
    """

    threaded = False

    @acquire_lock_in_first_thread
    def test_acquire_with_zero_timeeout(self, lock2):
        assert lock2.i_am_locking()
        self._assert_lock_acquired(lock2, 0)

    @acquire_lock_in_first_thread
    def test_acquire_with_negative_timeout(self, lock2):
        assert lock2.i_am_locking()
        self._assert_lock_acquired(lock2, -1)

    @acquire_lock_in_first_thread
    def test_acquire_with_positive_timeout(self, lock2):
        assert lock2.i_am_locking()
        self._assert_lock_acquired(lock2, 0.1)

    @acquire_lock_in_first_thread
    def test_init_with_positive_timeout(self, lock2):
        lock3 = self.class_to_test(self.test_file, threaded=self.threaded,
                                   timeout=0.2)
        assert lock3.is_locked()
        self._assert_lock_acquired(lock3, None)

    @acquire_lock_in_first_thread
    def test_release_from_other_lock(self, lock2):
        assert lock2.i_am_locking()
        lock2.release()
        assert not lock2.is_locked()
        assert not lock2.i_am_locking()


class ThreadDistinguishingTest(ComplianceTest):
    """
    Assertion tests for Lockfile objects that DO distinguish between
    threads in the same process.
    """

    threaded = True

    @acquire_lock_in_first_thread
    def test_acquire_with_zero_timeout(self, lock2):
        assert not lock2.i_am_locking()
        self._assert_already_locked(lock2, 0)

    @acquire_lock_in_first_thread
    def test_acquire_with_negative_timeout(self, lock2):
        assert not lock2.i_am_locking()
        self._assert_already_locked(lock2, -1)

    @acquire_lock_in_first_thread
    def test_acquire_with_positive_timeout(self, lock2):
        assert not lock2.i_am_locking()
        self._assert_lock_timeout(lock2, 0.1)

    @acquire_lock_in_first_thread
    def test_init_with_positive_timeout(self, lock2):
        lock3 = self.class_to_test(self.test_file, threaded=self.threaded,
                                   timeout=0.2)
        assert lock3.is_locked()
        self._assert_lock_timeout(lock3, None)

    @acquire_lock_in_first_thread
    def test_release_from_other_lock(self, lock2):
        assert not lock2.i_am_locking()
        try:
            lock2.release()
        except lockfile.NotMyLock:
            pass
        else:
            raise AssertionError('erroneously unlocked a file locked'
                                 ' by another thread.')


def _in_thread(func, *args, **kwargs):
    """Execute func(*args, **kwargs) after dt seconds. Helper for tests."""
    def _f():
        func(*args, **kwargs)
    t = threading.Thread(target=_f, name='/*/*')
    t.setDaemon(True)
    t.start()
    return t
