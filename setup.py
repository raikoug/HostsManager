from setuptools import find_packages, setup

setup(
    name='HostsManager',
    packages=find_packages(include=['HostsManager']),
    version='0.1.0',
    description='Windows and Linux hosts manager',
    author='Raikoug',
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
)