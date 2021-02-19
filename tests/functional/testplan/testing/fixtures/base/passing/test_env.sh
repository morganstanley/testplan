#!/bin/sh
if [ "$PROC_ENV1" != "abc" ]; then
  echo "Unexpected value of variable PROC_ENV1"
  exit 6
fi
if [ "$PROC_ENV2" != "123" ]; then
  echo "Unexpected value of variable PROC_ENV2"
  exit 7
fi
if [ "$DRIVER_MY_EXECUTABLE_ATTR_FOOBAR" != "foo bar" ]; then
  echo "Unexpected value of variable $DRIVER_MY_EXECUTABLE_ATTR_FOOBAR"
  exit 8
fi
if [ "$DRIVER_MY_EXECUTABLE_ATTR_MYVALUE" != "hello" ]; then
  echo "Unexpected value of variable $DRIVER_MY_EXECUTABLE_ATTR_VALUE"
  exit 9
fi
exit 0
