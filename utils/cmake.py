from dotenv import dotenv_values


def get_cmake_build_command(path: str):
    env = dotenv_values('.env')
    command = (
        env['CMAKE_PATH'],
        '-G',
        env['CMAKE_GENERATOR'],
        f'-DCMAKE_BUILD_TYPE={env["CMAKE_BUILD_TYPE"]}',
        '-DFETCH_GOOGLETEST=OFF',
        '-S',
        path,
        '-B',
        f'{path}/build',
    )
    return command


def get_cmake_make_command(path: str):
    env = dotenv_values('.env')
    command = (
        env['CMAKE_PATH'],
        '--build',
        f'{path}/build',
    )
    return command
