#!/usr/bin/env python

import click
from click import echo, confirm
import os, stat, re, sys
from os import path
from subprocess import call, Popen, PIPE
from shutil import copytree, rmtree
from pkg_resources import resource_filename
import yaml
from plaintable import Table

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
CT_PREFIX = 'CRONTAP_'

class Crontab(object):
    def __init__(self):
        pass
    def get_content(self, internal=True, external=False, withenv=False):
        p = Popen('crontab -l', stdout=PIPE, shell=True)
        output, err = p.communicate()
        output = output.strip().split('\n')
        if not internal:
            output = filter(lambda x: not CT_PREFIX in x, output)
        if not external:
            output = filter(lambda x: CT_PREFIX in x, output)
            if not withenv:
                output = filter(lambda x: not 'PATH=' in x, output)
        return output
    def write(self, s):
        p = Popen('crontab -', stdin=PIPE, shell=True)
        p.stdin.write("%s\n" % s)
        p.stdin.close()
    def load_modules(self, tap):
        to_write = []
        crontab_external = self.get_content(internal=False, external=True)
        to_write.append("PATH={path}:$PATH #{cmt}".format(path=os.getenv('PATH'), cmt=CT_PREFIX+'PATH'))
        to_write.append('\n'.join(crontab_external))
        for module_name in next(os.walk(tap.cronjob_dir))[1]:
            module = tap.Module(module_name)
            if not module.settings['enabled']:
                continue
            ## load into crontab
            schedule = module.settings['schedule']
            cmd = 'exec {path}'.format(path=module.strap_path)
            line = "{schedule} {cmd} #{cmt}".format(schedule=schedule, cmd=cmd, cmt=CT_PREFIX+module.name)
            to_write.append(line)
        self.write('\n'.join(to_write))
        tap.list_modules()

class Tap(object):
    def __init__(self, cronjob_dir):
        self.cronjob_dir = path.expanduser(cronjob_dir)
    def list_modules(self):
        if not list(os.walk(self.cronjob_dir))[0][1]:
            echo("No crontap module is installed.")
            return
        ## load crontab
        active_modules = {}
        crontab = Crontab()
        for line in crontab.get_content():
            ## refine later
            g = re.match("(.*)\sexec.*#%s(.*)" % CT_PREFIX, line)
            name = g.group(2)
            schedule = g.group(1)
            active_modules[name] = schedule
        headline = ['Module Name', 'Status', 'Schedule']
        data = []
        for module_name in next(os.walk(self.cronjob_dir))[1]:
            if active_modules.has_key(module_name):
                l = [module_name, 'ON', active_modules[module_name]]
            else:
                l = [module_name, 'OFF', '']
            data.append(l)
        echo(Table(data, headline))
    def Module(self, module_name):
        return Module(self, module_name)

class Module(object):
    def __init__(self, tap, module_name):
        self.name = module_name
        self.module_dir = path.join(tap.cronjob_dir, self.name)
        self.script_dir = path.join(self.module_dir, self.name)
        self.log_dir = path.join(self.module_dir, 'log')
        self.settings_path = path.join(self.script_dir, 'cron.yaml')
        self.strap_path = path.join(self.module_dir, 'cron.sh')
        if path.exists(self.module_dir):
            self.exists = True
            self.settings = yaml.load(open(self.settings_path, 'r'))
        else:
            self.exists = False
    def generate_bootstrap(self):
        strap_path = path.join(self.module_dir, 'cron.sh')
        cmd = self.settings['command']
        with open(strap_path, 'w') as f:
            cmd = ["cd '{dir}'".format(dir=self.script_dir, name=self.name), '&&',
                   '(', "date '+[%Y-%m-%d %H:%M:%S]'", ';', '{cmd}'.format(cmd=cmd), ';', 'echo ', "''", ')',
                   '1>> ../log/out.log', '2>> ../log/error.log']
            f.write('%s\n' % (' '.join(cmd)))
        st = os.stat(strap_path)
        os.chmod(strap_path, st.st_mode|stat.S_IEXEC)
        self.strap_path = strap_path
    def update_settings(self):
        with open(self.settings_path, 'w') as f:
            f.write(yaml.dump(self.settings, default_flow_style=False))

def reload_modules(tap):
    crontab = Crontab()
    crontab.load_modules(tap)

def is_valid_module(module_path):
    return path.exists(path.join(module_path, 'cron.yaml'))

@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx):
    '''crontap : crontab for Humans'''
    if os.environ.has_key('CRONTAP_MODULES'):
        modules_dir = os.environ['CRONTAP_MODULES']
    else:
        modules_dir = "~/.cronmodule"
    if not path.exists(path.abspath(path.expanduser(modules_dir))):
        e = "No cronmodule directory : '%s'" % path.abspath(path.expanduser(modules_dir))
        raise SystemExit, e
        return 1
    else:
        ctx.obj = Tap(modules_dir)

@cli.command('clear', help="Clear all crontap modules from crontab.")
@click.option('--hard', is_flag=True, help="Remove and uninstall all crontap module files too.")
@click.pass_obj
def clear_cmd(tap, hard):
    crontab = Crontab()
    externals = crontab.get_content(internal=False, external=True)
    s = '\n'.join(externals)
    crontab.write(s)
    echo("Cleared all crontap jobs.")
    if hard:
        for module_name in next(os.walk(tap.cronjob_dir))[1]:
            rmtree(path.join(tap.cronjob_dir, module_name))
        echo("Removed and uninstalled all crontap module files.")

@cli.command('disable', help="Disable <module_name>.")
@click.argument('module_name', metavar='<module_name>')
@click.pass_obj
def disable_cmd(tap, module_name):
    module = tap.Module(module_name)
    module.settings['enabled'] = False
    module.update_settings()
    echo("Disabled module '%s'." % module.name)
    reload_modules(tap)

@cli.command('enable', help="Enable <module_name>.")
@click.argument('module_name', metavar='<module_name>')
@click.pass_obj
def enable_cmd(tap, module_name):
    module = tap.Module(module_name)
    module.settings['enabled'] = True
    module.update_settings()
    echo("Enabled module '%s'." % module.name)
    reload_modules(tap)

@cli.command('init', help="Create a <module_name> template in CWD.")
@click.argument('module_name', metavar='<module_name>')
@click.pass_obj
def init_cmd(tap, module_name):
    if path.exists(module_name):
        confirm("Path '%s' already exists. Overwrite?" % module_name, abort=True)
        rmtree(module_name)
    # rewrite path
    template_dir = resource_filename(__name__, 'module_template')
    copytree(template_dir, module_name)
    echo("Created module template '%s' in the current working directory." % module_name)

@cli.command('list', help="List installed crontap modules.")
@click.pass_obj
def list_cmd(tap):
    tap.list_modules()

@cli.command('load', help="Reflect all crontap modules to crontab.")
@click.pass_obj
def load_cmd(tap):
    reload_modules(tap)

@cli.command('log', help="Show output log of <module_name>.")
@click.argument('module_name', metavar='<module_name>')
@click.option('--error', is_flag=True, help="Show error log.")
@click.option('--clear', is_flag=True, help="Clear log.")
@click.pass_obj
def log_cmd(tap, module_name, error, clear):
    module = tap.Module(module_name)
    if not module.exists:
        e = 'Usage: crontap log [OPTIONS] <module_name>\n\n' + \
            'Error: Invalid value for "module_name": Module "%s" is not installed.' % module.name
        raise SystemExit, e
    logfile = 'error.log' if error else 'out.log'
    if clear:
        open(path.join(module.log_dir, logfile), 'w').close()
        echo("Cleared '%s'." % logfile)
    else:
        with open(path.join(module.log_dir, logfile), 'r') as f:
            echo(f.read())

@cli.command('pull', help="Pull installed <module_name> to CWD.")
@click.argument('module_name', metavar='<module_name>')
@click.pass_obj
def pull_cmd(tap, module_name):
    module = tap.Module(module_name)
    if not module.exists:
        e = 'Usage: crontap pull [OPTIONS] <module_name>\n\n' + \
            'Error: Invalid value for "module_name": Module "%s" is not installed.' % module.name
        raise SystemExit, e
    if path.exists(module.name):
        confirm("Path '%s' already exists. Overwrite?" % module.name, abort=True)
        rmtree(module.name)
    copytree(module.script_dir, module.name)
    echo("Pulled module '%s' to the current working directory." % module.name)

@cli.command('push', help="Push and install <module_path>.")
@click.argument('module_path', metavar='<module_path>', type=click.Path(exists=True))
@click.pass_obj
def push_cmd(tap, module_path):
    if not is_valid_module(module_path):
        e = 'Usage: crontap pull [OPTIONS] <module_path>\n\n' + \
            'Error: Invalid value for "module_path": No cron.yaml in "%s".' % module_path
        raise SystemExit, e
    module = Module(tap, path.basename(module_path))
    if module.exists:
        confirm("Module '%s' is already installed. Overwrite?" % module.name, abort=True, default=True)
        rmtree(module.script_dir)
    else:
        os.makedirs(module.module_dir)
        os.makedirs(module.log_dir)
        open(path.join(module.log_dir, 'out.log'), 'a').close()
        open(path.join(module.log_dir, 'error.log'), 'a').close()
    copytree(module_path, module.script_dir)
    echo("Pushed and installed module '%s'." % module.name)
    module = Module(tap, module.name)
    module.generate_bootstrap()
    reload_modules(tap)

@cli.command('remove', help="Remove and uninstall <module_name>.")
@click.argument('module_name', metavar='<module_name>')
@click.pass_obj
def remove_cmd(tap, module_name):
    module = tap.Module(module_name)
    if not module.exists:
        e = 'Usage: crontap remove [OPTIONS] <module_name>\n\n' + \
            'Error: Invalid value for "module_name": Module "%s" is not installed.' % module.name
        raise SystemExit, e
    rmtree(module.module_dir)
    echo("Removed and uninstalled module '%s'." % module_name)
    reload_modules(tap)

@cli.command('run', help="Run installed <module_name> immediately.")
@click.argument('module_name', metavar='<module_name>')
@click.option('--log', is_flag=True, help="Use crontap log.")
@click.pass_obj
def run_cmd(tap, module_name, log):
    module = tap.Module(module_name)
    if not module.exists:
        e = 'Usage: crontap run [OPTIONS] <module_name>\n\n' + \
            'Error: Invalid value for "module_name": Module "%s" is not installed.' % module.name
        raise SystemExit, e
    if log:
        call(module.strap_path, shell=True)
    else:
        # test the command
        test_cmd = ["cd '{dir}'".format(dir=module.script_dir), '&&', '{cmd}'.format(cmd=module.settings['command'])]
        call(' '.join(test_cmd), shell=True)

if __name__ == '__main__':
    cli()
