#! /usr/bin/env python
# encoding: utf-8

import os
from waflib import Task, TaskGen

APPNAME = 'opus'
VERSION = '0.0.0'


# def configure(conf):

#     _set_simd_flags(conf)
#     if conf.is_mkspec_platform('linux') and not conf.env['LIB_PTHREAD']:
#         conf.check_cxx(lib='pthread')


def build(bld):
    bld.env.append_unique(
        'DEFINES_STEINWURF_VERSION',
        'STEINWURF_OPUS_VERSION="{}"'.format(VERSION))

    opus_path = bld.root.find_dir(bld.dependency_path('opus-source'))

    opus_cpp = opus_path.ant_glob('src/*.c')
    celt_cpp = opus_path.ant_glob('celt/*.c')
    silk_cpp = opus_path.ant_glob('silk/*.c')

    include_path = opus_path.find_dir('include/')
    celt_include_path = opus_path.find_dir('celt/')
    silk_include_path = opus_path.find_dir('silk/')
    includes = [
        opus_path,
        include_path,
        celt_include_path,
        silk_include_path]

    defines =[
        'USE_ALLOCA',
        'OPUS_BUILD',
        'PACKAGE_VERSION="1.3.1"'
    ]

    fixed_point = False

    if fixed_point:
        includes += [opus_path.find_dir('silk/fixed')]
        silk_cpp += opus_path.ant_glob('silk/fixed/*.c')
        defines += ['FIXED_POINT']
    else:
        includes += [opus_path.find_dir('silk/float')]
        silk_cpp += opus_path.ant_glob('silk/float/*.c')

    bld.stlib(
        features='c',
        source=opus_cpp + celt_cpp + silk_cpp,
        includes=includes,
        target='opus',
        defines=defines,
        export_includes=includes)

    if bld.is_toplevel():
        # Only build tests when executed from the top-level wscript,
        # i.e. not when included as a dependency

        common = opus_path.ant_glob('tests/opus_encode_regressions.c')

        bld.program(
            features='cxx test',
            source=common + opus_path.ant_glob('tests/test_opus_padding.c'),
            target='test_opus_padding',
            use=['opus'])

        bld.program(
            features='cxx test',
            source=common + opus_path.ant_glob('tests/test_opus_decode.c'),
            target='test_opus_decode',
            use=['opus'])

        bld.program(
            features='cxx test',
            source=common + opus_path.ant_glob('tests/test_opus_api.c'),
            target='test_opus_api',
            use=['opus'])

        bld.program(
            features='cxx test',
            source=common + opus_path.ant_glob('tests/test_opus_encode.c'),
            target='test_opus_encode',
            use=['opus'])

        bld.program(
            features='cxx test',
            source=common + opus_path.ant_glob('tests/test_opus_projection.c'),
            target='test_opus_projection',
            use=['opus'])

def _set_simd_flags(conf):
    """
    Sets flags used to compile in SIMD mode
    """
    CXX = conf.env.get_flat("CXX")
    flags = []
    # DEST_CPU should be set explicitly for clang cross-compilers
    cpu = conf.env['DEST_CPU']

    print("CPU = {}".format(cpu))

    # Matches both g++ and clang++
    if 'g++' in CXX or 'clang' in CXX:
        # Test different compiler flags based on the target CPU
        if cpu == 'x86' or cpu == 'x86_64':
            flags += conf.mkspec_try_flags(
                'cxxflags', ['-msse2', '-mssse3', '-msse4.2', '-mavx2'])
        elif cpu == 'arm':
            flags += conf.mkspec_try_flags('cxxflags', ['-mfpu=neon'])

    elif 'CL.exe' in CXX or 'cl.exe' in CXX:
        if cpu == 'x86' or cpu == 'x86_64' or cpu == 'amd64':
            flags += conf.mkspec_try_flags('cxxflags', ['/arch:AVX2'])

    elif 'em++' in CXX:
        flags = []

    else:
        conf.fatal('Unknown compiler - no SIMD flags specified')

    conf.env['CFLAGS_FIFI_SIMD'] = flags
    conf.env['CXXFLAGS_FIFI_SIMD'] = flags
