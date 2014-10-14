from pip.req import parse_requirements
import setuptools

reqs = [str(ir.req) for ir in parse_requirements('requirements.txt')]

setuptools.setup(name='mixcloud',
                 version='0.0+dev',
                 packages=['mixcloud'],
                 install_requires=reqs,
                 )
