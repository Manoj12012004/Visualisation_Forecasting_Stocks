from setuptools import find_packages, setup


def get_requirements(file_path: str) -> list:
    """
    This function returns a list of requirements from the given file path.
    :param file_path: str: Path to the requirements file
    :return: list: List of requirements
    """
    with open(file_path) as file_obj:
        requirements = file_obj.readlines()
        requirements = [req.replace("\n", "") for req in requirements]
        if '-e .' in requirements:
            requirements.remove('-e .')
    return requirements

setup(
    name='mlproject',
    version='0.1.0',
    author='manojkumar',
    author_email="sandupatlamanojkumar@gmail.com",
    packages=find_packages(),
    install_requires=get_requirements('requirements.txt'),
) 