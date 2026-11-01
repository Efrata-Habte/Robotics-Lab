from setuptools import find_packages, setup

package_name = 'my_robot_nodes'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='makrina',
    maintainer_email='efratahabte1213@gmail.com',
    description='Nodes and launch file for the lab 1 exercise',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'turn_away = my_robot_nodes.turn_away:main',
            'rotate_server = my_robot_nodes.rotate_server:main',
        ],
    },
)
