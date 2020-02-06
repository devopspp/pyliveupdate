import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyliveupdate", 
    version="0.1.2",
    author="devopspp",
    keywords='runtime instrumentation logging profiling debugging',
    description="A tool to manipulate python code at runtime for logging, profiling, debugging, etc.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/devopspp/pyliveupdate",
    license='GPLv3',
    packages=setuptools.find_packages(exclude=['tests', 'experimental', 'examples']),
    python_requires='>=3.6',
    install_requires=[
        'bytecode',
        'stdlib_list',
      ],
    entry_points="""
          [console_scripts]
          pylu-controller = pyliveupdate.startcontroller:main
      """,
    classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Topic :: System :: Logging',
          'Topic :: System :: Monitoring',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: Debuggers',
          'Programming Language :: Python :: 3',
      ]
)
