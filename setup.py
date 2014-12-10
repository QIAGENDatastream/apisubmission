from setuptools import setup

setup(name='ingapi',
        version='0.1',
        description='Ingenuity Upload and Status Python Helper scripts and DatastreamAPI library',
        url='localhost', #FIXME
        author="Chris Harris",
        author_email="charris@bigelow.org",
        license="GPLv3",
        packages=['ingapi'],
        install_requires=['requests',
            'logging',
            ],

        scripts=['bin/upload.py',
                 'bin/status.py',
                    ],
        zip_safe=False)
