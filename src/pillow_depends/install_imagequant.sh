#!/bin/bash
# install libimagequant

archive=libimagequant-2.12.2

./download-and-extract.sh $archive https://raw.githubusercontent.com/python-pillow/pillow-depends/master/$archive.tar.gz

pushd $archive

make shared
cp libimagequant.so* /usr/lib/
cp libimagequant.h /usr/include/

popd
