#!/bin/bash

python setup.py sdist
VERSION=$(ls dist/*.tar.gz | tail -n 1 | sed -ne 's/[^-]*-\(.*\).tar.gz/\1/p')
cp dist/bauble-${VERSION}.tar.gz /tmp/bauble-${VERSION}.orig.tar.gz
( cd /tmp
  rm -fr bauble-${VERSION}/
  tar zxf bauble-${VERSION}.orig.tar.gz 
  cd bauble-${VERSION}/
  dh_make --yes --indep --file ../bauble-${VERSION}.orig.tar.gz )
cp debian/* /tmp/bauble-${VERSION}/debian
rm /tmp/bauble-${VERSION}/debian/*.{ex,EX,source}
cd /tmp/bauble-${VERSION}/
debuild
