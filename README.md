crontap : crontab for Humans
====

crontap is a modular, git-like and easy-to-use crontab management tool for you. (not for machines!)

Installation
----

```bash
sudo pip install git+https://github.com/nolze/crontap
mkdir ~/.cronmodule
```

or

```bash
git clone https://github.com/nolze/crontap && cd crontap
python setup.py install
mkdir ~/.cronmodule
```


### Uninstall

```bash
sudo pip uninstall crontap
rm -rf ~/.cronmodule
# if you don't need them:
sudo pip uninstall Click pyyaml plaintable
```

Example Usage
----

### Make a cronjob module (cronmodule)

Let's check [the utaskun pics](http://www.c.u-tokyo.ac.jp/zenki/utasukun/index.html) everyday, and save it if is updated.

#### 1. Create a new module from template in some directory.

```bash
$ cd some_working_dir
$ crontap init utaskun
Created module template 'utaskun' in the current working directory.
$ cd utaskun
```

#### 2. Write and setup your routine scripts.

get_utaskun.sh
```bash
#!/bin/bash

set -u

cd /tmp;
wget http://www.c.u-tokyo.ac.jp/zenki/utasukun/utaskun.gif -O utaskun.gif
find ~/Downloads/utaskun_collection/ -type f -exec md5 -q {} + | grep -sqE `md5 -q utaskun.gif`
if [[ $? != 0 ]]; then
  date +'%Y%m%d' | xargs -I{} mv utaskun.gif ~/Downloads/utaskun_collection/{}.gif
  echo "A new utaskun pic is found and downloaded."
else
  echo "No new utaskun pic is found."
fi
```

cron.yaml
```yaml
enabled: True
command: "./get_utaskun.sh"
schedule: "0 0 * * *" # run every midnight, if your machine is up
```

```bash
$ mkdir ~/Downloads/utaskun_collection
```

#### 3. Test your scripts.

```bash
$ chmod +x get_utaskun.sh
$ ./get_utaskun.sh
...
A new utaskun pic is found and downloaded.
```

#### 4. Push (install) module.

```bash
$ cd ..
$ crontap push utaskun
Pushed and installed module 'utaskun'.
Module Name Status  Schedule
----------- ------  ---------
utaskun     ON      0 0 * * *
```

#### Done!

```bash
$ crontap list
Module Name Status  Schedule
----------- ------  ---------
utaskun     ON      0 0 * * *
$ crontap run utaskun # try running it now
...
No new utaskun pic is found.
$ crontap run utaskun --log # with redirecting outputs to crontap logs
```

### Enable / Disable a module

```bash
$ crontap enable utaskun
Enabled module 'utaskun'.
...
$ crontap disable utaskun
Disabled module 'utaskun'.
Module Name Status  Schedule
----------- ------  --------
utaskun     OFF
$ crontap clear # clear all modules from crontab
Cleared all crontap jobs.
$ crontap load # reflect all modules to crontab
Module Name Status  Schedule
----------- ------  --------
utaskun     OFF
```


### Update a module

#### 1. Pull it.

```bash
$ crontap pull utaskun
Path 'utaskun' already exists. Overwrite? [y/N]: y
Pulled module 'utaskun' to the current working directory.
```

#### 2. Edit scripts.

get_utaskun.rb
```ruby
#!/bin/ruby
...
```

cron.yaml
```yaml
enabled: false
command: "ruby get_utaskun.rb"
schedule: "0 0 * * *"
```

#### 3. Re-push revised module.

```bash
$ crontap push utaskun
Module 'utaskun' is already installed. Overwrite? [Y/n]: 
Module Name Status  Schedule
----------- ------  --------
utaskun     OFF
```

### Check output logs

```bash
$ crontap log utaskun
[2015-02-18 23:14:37]
No new utaskun pic is found.
$ crontap log utaskun > log.txt # save log
$ crontap log utaskun --error # show error log
...
$ crontap log utaskun --clear --error # clear error log
Cleared 'error.log'.
```

### Remove (uninstall) a module

```bash
$ crontap remove utaskun
Removed and uninstalled module 'utaskun'.
...
$ crontap clear --hard # delete all module files
Removed and uninstalled all crontap module files.
```

LICENSE
----

GPLv3

