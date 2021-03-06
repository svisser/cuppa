
#          Copyright Jamie Allsop 2011-2014
# Distributed under the Boost Software License, Version 1.0.
#    (See accompanying file LICENSE_1_0.txt or copy at
#          http://www.boost.org/LICENSE_1_0.txt)

#-------------------------------------------------------------------------------
#   Registraion
#-------------------------------------------------------------------------------

def get_module_list( path, base=None ):
    from os import listdir
    from re import match
    from os.path import dirname
    paths = listdir( dirname( path ) )

    def unique( seq ):
        seen = set()
        seen_add = seen.add
        return [ x for x in seq if x not in seen and not seen_add(x) ]

    return unique( [ base and '.'.join( [ base, f.replace('.py','') ] ) or f.replace('.py','') for f in paths for f in paths if match( '[^_.~].*\.py$', f ) ] )


def add_to_env( module_name, args ):
    __call_classmethod_for_classes_in_module( 'cuppa', module_name, __package('cuppa'), "add_to_env", args )


def add_options( module_name ):
    __call_classmethod_for_classes_in_module( 'cuppa', module_name, __package('cuppa'), "add_options", None )


def init_env_for_variant( module_name, args ):
    __call_classmethod_for_classes_in_module( 'cuppa', module_name, __package('cuppa'), "init_env_for_variant", args )


#-------------------------------------------------------------------------------

import inspect
import imp
import sys

def __package( name ):
    package = None
    try:
        filehandle, pathname, description = imp.find_module( name, None )
        try:
            try:
                module = sys.modules[ name ]
            except KeyError, (e):
                module = imp.load_module( name, filehandle, pathname, description )
            package = pathname
        finally:
            if filehandle:
                filehandle.close()
    except ImportError, (e):
        pass

    return package


def __call_classmethod_for_classes_in_module( package, name, path, method, args ):
    try:
        filehandle, pathname, description = imp.find_module( name, path and [ path ] or None )
        try:
            try:
                qualified_name = package and package + "." + name or name
                module = sys.modules[ qualified_name ]

            except KeyError, (e):
                module = imp.load_module( name, filehandle, pathname, description )

            for member_name in dir( module ):

                member = getattr( module, member_name )

                if inspect.ismodule( member ):
                    if package:
                        parent_package = package + "." + name
                    else:
                        parent_package = name
                    __call_classmethod_for_classes_in_module( parent_package, member_name, pathname, method, args )

                elif inspect.isclass( member ):
                    try:
                        function = getattr( member, method )
                        if callable( function ):
                            if( args ):
                                function( args )
                            else:
                                function()
                    except AttributeError, (e):
                        pass
        finally:
            if filehandle:
                filehandle.close()

    except ImportError, (e):
        pass

#-------------------------------------------------------------------------------
