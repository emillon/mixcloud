from pip.req import parse_requirements
import setuptools

with open('README.rst') as f:
    readme = f.read()

with open('HISTORY.rst') as f:
    history = f.read()

setuptools.setup(name='mixcloud',
                 version='0.0.3+dev',
                 author='Etienne Millon',
                 author_email='me@emillon.org',
                 url="https://github.com/emillon/mixcloud",
                 license='BSD',
                 packages=['mixcloud'],
                 install_requires=[
                     'python-dateutil',
                     'requests',
                     'unidecode',
                     'pyyaml',
                 ],
                 description='Bindings for the mixcloud.com API',
                 long_description=readme + '\n\n' + history,
                 classifiers=[
                     'Development Status :: 3 - Alpha',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: BSD License',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python :: 2',
                     'Programming Language :: Python :: 3',
                     ],
                 )
