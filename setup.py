from pip.req import parse_requirements
import setuptools

reqs = [str(ir.req) for ir in parse_requirements('requirements.txt')]

with open('README.rst') as f:
    readme = f.read()

with open('HISTORY.rst') as f:
    history = f.read()

setuptools.setup(name='mixcloud',
                 version='0.0+dev',
                 packages=['mixcloud'],
                 install_requires=reqs,
                 description='Bindings for the mixcloud.com API',
                 long_description=readme + '\n\n' + history,
                 )
