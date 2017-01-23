from spec import skip, Spec, ok_, eq_
from invoke import pty_size

from fabric import Connection, Group


class Connection_(Spec):
    class ssh_connections:
        def open_method_generates_real_connection(self):
            c = Connection('localhost')
            c.open()
            eq_(c.client.get_transport().active, True)
            eq_(c.is_connected, True)
            return c

        def close_method_closes_connection(self):
            # Handy shortcut - open things up, then return Connection for us to
            # close
            c = self.open_method_generates_real_connection()
            c.close()
            eq_(c.client.get_transport(), None)
            eq_(c.is_connected, False)

    class run:
        def simple_command_on_host(self):
            """
            Run command on localhost
            """
            result = Connection('localhost').run('echo foo', hide=True)
            eq_(result.stdout, "foo\n")
            eq_(result.exited, 0)
            eq_(result.ok, True)

        def simple_command_with_pty(self):
            """
            Run command under PTY on localhost
            """
            # Most Unix systems should have stty, which asplodes when not run
            # under a pty, and prints useful info otherwise
            result = Connection('localhost').run(
                'stty -a', hide=True, pty=True,
            )
            cols, rows = pty_size()
            ok_("{0} rows; {1} columns;".format(rows, cols) in result.stdout)
            # PTYs use \r\n, not \n, line separation
            ok_("\r\n" in result.stdout)
            eq_(result.pty, True)

    class local:
        def wraps_invoke_run(self):
            # NOTE: most of the interesting tests about this are in
            # invoke.runners / invoke.integration.
            cxn = Connection('localhost')
            result = cxn.local('echo foo', hide=True)
            eq_(result.stdout, 'foo\n')
            assert not cxn.is_connected # meh way of proving it didn't use SSH

    def mixed_use_of_local_and_run(self):
        """
        Run command truly locally, and over SSH via localhost
        """
        cxn = Connection('localhost')
        result = cxn.local('echo foo', hide=True)
        eq_(result.stdout, 'foo\n')
        assert not cxn.is_connected # meh way of proving it didn't use SSH yet
        result = cxn.run('echo foo', hide=True)
        assert cxn.is_connected # NOW it's using SSH
        eq_(result.stdout, 'foo\n')

    class sudo:
        # TODO: set up the Travis-level changes from
        # https://github.com/pyinvoke/invoke/issues/366 - tl;dr these tests
        # get skipped when run on a workstation but get run under Travis, and
        # require the test suite to be set up with a known-password,
        # passworded-sudo user.

        def sudo_command(self):
            """
            Run command via sudo on host localhost
            """
            skip()
            eq_(
                Connection('localhost').sudo('whoami').stdout,
                'root\n',
            )

        def mixed_sudo_and_normal_commands(self):
            """
            Run command via sudo, and not via sudo, on localhost
            """
            skip()
            cxn = Connection('localhost')
            cxn.run('whoami')
            cxn.sudo('whoami')
            # Alternately...
            cxn.run('whoami', runner=Basic) # noqa
            cxn.run('whoami', runner=Sudo) # noqa


class Group_(Spec):
    def simple_command_on_multiple_hosts(self):
        """
        Run command on localhost...twice!
        """
        group = Group(['localhost', 'localhost'])
        result = group.run('echo foo', hide=True)
        # NOTE: currently, the result will only be 1 object, because both of
        # them will end up as the same key. Derp.
        eq_(result[group[0]].stdout, "foo\n")
