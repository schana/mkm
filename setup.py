from setuptools import setup, find_packages

setup(
    name='manager',
    version='0.0.1',
    description='',
    packages=find_packages(exclude=['test', 'test.*', '*.test']),
    install_requires=[
        'requests',
        'requests-oauthlib',
        'pprint'
    ]
)
