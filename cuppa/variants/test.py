
#          Copyright Jamie Allsop 2011-2014
# Distributed under the Boost Software License, Version 1.0.
#    (See accompanying file LICENSE_1_0.txt or copy at
#          http://www.boost.org/LICENSE_1_0.txt)

#-------------------------------------------------------------------------------
#   Test
#-------------------------------------------------------------------------------

# Scons
import SCons.Script

class Test:

    @classmethod
    def name( cls ):
        return cls.__name__.lower()


    @classmethod
    def add_options( cls ):
        SCons.Script.AddOption(
                '--test', dest=cls.name(), action='store_true',
                help='Run the binary as a test' )


    @classmethod
    def add_to_env( cls, args ):
        args['env']['actions'][cls.name()] = cls()


