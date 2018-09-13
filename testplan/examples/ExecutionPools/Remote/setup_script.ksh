#!/bin/ksh
echo 'Executing setup commands.'

echo 'Environment:'
env

echo 'User:'
echo $USER

echo 'Hostname:'
hostname

# Make a soft link in remote host to make the local workspace
# absolute path available for hardcoded entries.
if [ ! -d $TESTPLAN_LOCAL_WORKSPACE ];
then
    mkdir -p `dirname $TESTPLAN_LOCAL_WORKSPACE`
    ln -s $TESTPLAN_REMOTE_WORKSPACE $TESTPLAN_LOCAL_WORKSPACE
else
    echo 'Local workspace is visible from the remote!'
fi

echo 'Finished setup commands.'
exit 0