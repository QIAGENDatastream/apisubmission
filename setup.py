from setuptools import setup

setup(name='dsapi',
        version='0.4',
        description='Ingenuity Upload and Status Python Helper scripts and DatastreamAPI library',
        url='localhost', #FIXME
        author="Chris Harris",
        author_email="charris@ingenuity.com",
        license="GPLv3",
        packages=['dsapi'],
        install_requires=['requests',
            'logging',
            'pygments',
            ],

        scripts=['bin/ds_upload.py',
                 'bin/ds_status.py',
                    ],
        zip_safe=False)
