#          Copyright Jamie Allsop 2011-2014
# Distributed under the Boost Software License, Version 1.0.
#    (See accompanying file LICENSE_1_0.txt or copy at
#          http://www.boost.org/LICENSE_1_0.txt)

#-------------------------------------------------------------------------------
#   Core
#-------------------------------------------------------------------------------

# Python Standard
import os.path
import inspect
import os
import re
import fnmatch

# Scons
import SCons.Script

# Custom
import cuppa.modules.registration
import cuppa.build_platform
import cuppa.output_processor
import cuppa.colourise
import cuppa.recursive_glob
import cuppa.configure
import cuppa.options
import cuppa.version

from cuppa.scms                   import *
from cuppa.toolchains             import *
from cuppa.methods                import *
from cuppa.dependencies           import *
from cuppa.profiles               import *
from cuppa.variants               import *
from cuppa.project_generators     import *


SCons.Script.Decider( 'MD5-timestamp' )




def add_base_options():

    SCons.Script.AddOption( '--raw-output', dest='raw_output', action='store_true',
                            help='Disable output processing like colourisation of output' )

    SCons.Script.AddOption( '--standard-output', dest='standard_output', action='store_true',
                            help='Perform standard output processing but not colourisation of output' )

    SCons.Script.AddOption( '--minimal-output', dest='minimal_output', action='store_true',
                            help='Show only errors and warnings in the output' )

    SCons.Script.AddOption( '--ignore-duplicates', dest='ignore_duplicates', action='store_true',
                            help='Do not show repeated errors or warnings' )

    SCons.Script.AddOption( '--projects', type='string', nargs=1,
                            action='callback', callback=cuppa.options.list_parser( 'projects' ),
                            help='Projects to build (alias for scripts)' )

    SCons.Script.AddOption( '--scripts', type='string', nargs=1,
                            action='callback', callback=cuppa.options.list_parser( 'projects' ),
                            help='Sconscripts to run' )

    SCons.Script.AddOption( '--thirdparty', type='string', nargs=1, action='store',
                            dest='thirdparty',
                            metavar='DIR',
                            help='Thirdparty directory' )

    SCons.Script.AddOption( '--build-root', type='string', nargs=1, action='store',
                            dest='build_root',
                            help='The root directory for build output. If not specified then .build is used' )

    SCons.Script.AddOption( '--runner', type='string', nargs=1, action='store',
                            dest='runner',
                            help='The test runner to use for executing tests. The default is the process test runner' )

#    SCons.Script.AddOption( '--decider', dest='decider', type='string', nargs=1, action='store',
#                            help='The decider to use for determining if a dependency has changed',
#                            default = 'MD5-timestamp' )



def set_base_options():
    SCons.Script.SetOption( 'warn', 'no-duplicate-environment' )



class ConstructException(Exception):

    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)



class ParseToolchainsOption(object):

    def __init__( self, supported_toolchains, available_toolchains ):
        self._supported = supported_toolchains
        self._available = available_toolchains

    def __call__(self, option, opt, value, parser):
        toolchains = set()
        requested = value.split(',')
        for toolchain in requested:
            supported = fnmatch.filter( self._supported, toolchain )

            if not supported:
                print "cuppa: requested toolchain(s) [{}] does not match any supported, skipping".format( toolchain )
            else:
                available = fnmatch.filter( self._available, toolchain )

                if not available:
                    print "cuppa: requested toolchain(s) [{}] supported does not match any available, skipping".format( toolchain )
                else:
                    toolchains.update( available )

        if not toolchains:
            print "cuppa: None of the requested toolchains are available"

        parser.values.toolchains = list(toolchains)


class Construct(object):

    platforms_key    = 'platforms'
    variants_key     = 'variants'
    actions_key      = 'actions'
    toolchains_key   = 'toolchains'
    scm_systems_key  = 'scms'
    dependencies_key = 'dependencies'
    profiles_key     = 'profiles'
    project_generators_key = 'project_generators'


    @classmethod
    def get_option( cls, env, option, default=None ):
        value = SCons.Script.GetOption( option )
        source = None
        colouriser = env['colouriser']
        if value == None or value == '':
            if env['default_options'] and option in env['default_options']:
                value = env['default_options'][ option ]
                source = "in the sconstruct file"
            elif default:
                value = default
                source = "using default"
        else:
            source = "on command-line"

        if option in env['configured_options']:
            source = "using configure"

        if value:
            print "cuppa: option [{}] set {} as [{}]".format(
                        colouriser.colour( 'warning', option ),
                        source,
                        colouriser.colour( 'warning', str(value) ) )
        return value


    def add_platforms( self, env ):
        platforms = self.platforms_key
        env[platforms] = cuppa.build_platform.Platform.supported()


    def add_project_generators( self, env ):
        project_generators = self.project_generators_key
        env[project_generators] = {}
        cuppa.modules.registration.add_to_env( project_generators, { 'env': env } )


    def add_scm_systems( self, env ):
        scms = self.scm_systems_key
        env[scms] = {}
        cuppa.modules.registration.add_to_env( scms, { 'env': env } )

        SCons.Script.AddOption(
            '--scm',
            dest    = 'scm',
            nargs   = 1,
            action  = 'store',
            choices = env[scms].keys(),
            help    = 'The Source Control Management System we are using' )

        cuppa.modules.registration.add_options( scms )


    def add_variants( self, env ):
        variants = self.variants_key
        actions  = self.actions_key
        env[variants] = {}
        env[actions]  = {}
        cuppa.modules.registration.add_to_env( variants, { 'env': env } )
        cuppa.modules.registration.add_options( variants )



    def add_toolchains( self, env ):
        toolchains = self.toolchains_key
        env[toolchains] = {}
        env['supported_toolchains'] = []
        cuppa.modules.registration.add_to_env( toolchains, { 'env': env } )

        colouriser = env['colouriser']
        print "cuppa: supported toolchains are {}".format( colouriser.colour( 'notice', str( env["supported_toolchains"] ) ) )
        print "cuppa: available toolchains are {}".format( colouriser.colour( 'warning', str( env[toolchains].keys() ) ) )

        SCons.Script.AddOption(
            '--toolchains',
            type     = 'string',
            nargs    = 1,
            action   = 'callback',
            callback = ParseToolchainsOption( env['supported_toolchains'], env[toolchains].keys() ),
            help     = 'The Toolchains you wish to build against' )


    def initialise_options( self, env, default_options ):
        env['default_options'] = default_options or {}

        env.AddMethod( self.get_option, "get_option" )

        add_base_options()
        cuppa.modules.registration.add_options( self.toolchains_key )
        cuppa.modules.registration.add_options( self.scm_systems_key )
        cuppa.modules.registration.add_options( self.dependencies_key )
        cuppa.modules.registration.add_options( self.profiles_key )
        cuppa.modules.registration.add_options( self.project_generators_key )


    def print_construct_variables( self, env ):
        keys = {
                'raw_output',
                'standard_output',
                'minimal_output',
                'ignore_duplicates',
                'working_dir',
                'launch_dir',
                'launch_offset_dir',
                'run_from_launch_dir',
                'base_path',
                'branch_root',
                'branch_dir',
                'thirdparty',
                'build_root',
                'default_dependencies',
                'BUILD_WITH',
                'dependencies',
                'sconscript_dir',
                'sconscript_file',
                'build_dir',
                'offset_dir',
        }

        for key in keys:
            print "cuppa: Env[%s] = %s" % ( key, env[key] )


    def __init__( self,
                  base_path            = os.path.abspath( '.' ),
                  branch_root          = os.path.abspath( '.' ),
                  default_options      = None,
                  default_projects     = None,
                  default_variants     = None,
                  default_dependencies = None,
                  default_profiles     = None,
                  default_runner       = None,
                  configure_callback   = None ):

        print "cuppa: version {}".format( cuppa.version.get() )

        set_base_options()

        self._default_env = SCons.Script.DefaultEnvironment()
        default_env = self._default_env

        self.initialise_options( default_env, default_options )

        default_env['configured_options'] = {}

        default_env['colouriser'] = cuppa.colourise.Colouriser.create()

        self._configure = cuppa.configure.Configure( default_env, callback=configure_callback )

        default_env['raw_output']      = default_env.get_option( 'raw_output' ) and True or False
        default_env['standard_output'] = default_env.get_option( 'standard_output' ) and True or False

        if not default_env['raw_output'] and not default_env['standard_output']:
            default_env['colouriser'].enable()

        help = default_env.get_option( 'help' ) and True or False

        self._configure.load()

        default_env['minimal_output']       = default_env.get_option( 'minimal_output' )
        default_env['ignore_duplicates']    = default_env.get_option( 'ignore_duplicates' )

        default_env['working_dir']          = os.getcwd()
        default_env['launch_dir']           = os.path.relpath( SCons.Script.GetLaunchDir(), default_env['working_dir'] )
        default_env['run_from_launch_dir']  = default_env['launch_dir'] == "."

        default_env['launch_offset_dir']    = "."

        if not default_env['run_from_launch_dir']:
            levels = len( default_env['launch_dir'].split( os.path.sep ) )
            default_env['launch_offset_dir'] = os.path.sep.join( ['..' for i in range(levels)] )

        default_env['base_path']            = base_path
        default_env['branch_root']          = branch_root
        default_env['branch_dir']           = os.path.relpath( base_path, branch_root )
        default_env['thirdparty']           = default_env.get_option( 'thirdparty' )
        default_env['build_root']           = default_env.get_option( 'build_root', default='.build' )
        default_env['default_projects']     = default_projects
        default_env['default_variants']     = default_variants and set( default_variants ) or set()
        default_env['default_dependencies'] = default_dependencies and default_dependencies or []
        default_env['BUILD_WITH']           = default_env['default_dependencies']
        default_env['dependencies']         = {}
        default_env['default_profiles']     = default_profiles and default_profiles or []
        default_env['BUILD_PROFILE']        = default_env['default_profiles']
        default_env['profiles']             = {}

        test_runner = default_env.get_option( 'runner', default=default_runner and default_runner or 'process' )
        default_env['default_runner']  = test_runner

        self.add_variants   ( default_env )
        self.add_toolchains ( default_env )
        self.add_platforms  ( default_env )

        self.add_project_generators( default_env )

        default_env['platform'] = cuppa.build_platform.Platform.current()

        self.add_scm_systems( default_env )

        scm_system = default_env.get_option( 'scm' )

        default_env['scm'] = ( scm_system and default_env[self.scm_systems_key][ scm_system ]
                                          or  None )

        toolchains = default_env.get_option( 'toolchains' )

        default_toolchain = default_env['platform'].default_toolchain()

        if not toolchains:
            toolchains = [ default_env[self.toolchains_key][default_toolchain] ]
        else:
            toolchains = [ default_env[self.toolchains_key][t] for t in toolchains ]

        default_env['active_toolchains'] = toolchains

        cuppa.modules.registration.add_to_env( "dependencies",       { 'env': default_env } )
        cuppa.modules.registration.add_to_env( "profiles",           { 'env': default_env } )
        cuppa.modules.registration.add_to_env( "methods",            { 'env': default_env } )
        cuppa.modules.registration.add_to_env( "project_generators", { 'env': default_env } )

        # TODO - default_profile

        if not help and self._configure.handle_conf_only():
            self._configure.save()

        if not help and not self._configure.handle_conf_only():
            self.build( default_env )

        if self._configure.handle_conf_only():
            print "cuppa: Handling onfiguration only, so no builds will be attempted."
            print "cuppa: With the current configuration executing 'scons -D' would be equivalent to:"
            print ""
            print "scons -D {}".format( self._command_line_from_settings( default_env['configured_options'] ) )
            print ""
            print "cuppa: Nothing to be done. Exiting."
            SCons.Script.Exit()


    def _as_emphasised( self, text ):
        return self._default_env['colouriser'].emphasise( text )


    def _as_error( self, text ):
        return self._default_env['colouriser'].colour( 'error', text )


    def _as_warning( self, text ):
        return self._default_env['colouriser'].colour( 'warning', text )


    def _as_notice( self, text ):
        return self._default_env['colouriser'].colour( 'notice', text )


    def _command_line_from_settings( self, settings ):
        commands = []
        for key, value in settings.iteritems():
            command = self._as_emphasised( "--" + key )
            if value != True and value != False:
                if not isinstance( value, list ):
                    command += "=" + self._as_warning( str(value) )
                else:
                    command += "=" + self._as_warning( ",".join( value ) )
            commands.append( command )
        commands.sort()
        return " ".join( commands )


    def get_active_actions_for_variant( self, default_env, active_variants, variant ):
        available_variants = default_env[ self.variants_key ]
        available_actions  = default_env[ self.actions_key ]
        specified_actions  = {}

        for key, action in available_actions.items():
            if default_env.get_option( action.name() ):
                specified_actions[ action.name() ] = action

        if not specified_actions:
            default_variants = active_variants
            if default_variants:
                for variant in default_variants:
                    if available_actions.has_key( variant ):
                        specified_actions[ variant ] = available_actions[ variant ]

        active_actions = {}

        for key, action in specified_actions.items():
            if key not in available_variants:
                active_actions[ key ] = action
            elif key == variant.name():
                active_actions[ key ] = action

        return active_actions


    def create_build_variants( self, toolchain, default_env ):

        variants  = default_env[ self.variants_key ]

        active_variants = {}

        for key, variant in variants.items():
            if default_env.get_option( variant.name() ):
                active_variants[ variant.name() ] = variant

        if not active_variants:
            default_variants = default_env['default_variants'] or toolchain.default_variants()
            if default_variants:
                for variant in default_variants:
                    if variants.has_key( variant ):
                        active_variants[ variant ] = variants[ variant ]

        variant_envs = {}

        for key, variant in active_variants.items():
            variant_envs[ key ] = variant.create( default_env.Clone(), toolchain )

            if not default_env['raw_output']:
                cuppa.output_processor.Processor.install( variant_envs[ key ] )

            variant_envs[ key ]['toolchain'] = toolchain
            variant_envs[ key ]['variant'] = variant
            variant_envs[ key ]['variant_actions'] = self.get_active_actions_for_variant( default_env, active_variants, variant )

        return variant_envs


    def get_sub_sconscripts( self, path ):
        regex = re.compile( r'([^.]+[.])?sconscript$', re.IGNORECASE )
        return cuppa.recursive_glob.glob(path, regex )


    def colour_items( self, items ):
        return "'{}'".format( "', '".join( self._as_notice( item ) for item in items ) )


    def build( self, default_env ):

        projects   = default_env.get_option( 'projects' )
        colouriser = default_env['colouriser']
        toolchains = default_env['active_toolchains']

        if projects == None:
            projects = default_env['default_projects']

            if projects == None or not default_env['run_from_launch_dir']:
                sub_sconscripts = self.get_sub_sconscripts( default_env['launch_dir'] )
                if sub_sconscripts:
                    projects = sub_sconscripts
                    print "cuppa: Using sub-sconscripts [{}]".format( self.colour_items( projects ) )
            elif projects != None:
                print "cuppa: Using default_projects [{}]".format( self.colour_items( projects ) )

        if projects:

            sconscripts = []

            for project in projects:
                if os.path.exists( project ) and os.path.isdir( project ):
                    sub_sconscripts = self.get_sub_sconscripts( project )
                    if sub_sconscripts:
                        print "cuppa: Reading project folder [{}] and using sub-sconscripts [{}]".format(
                                project, self.colour_items( sub_sconscripts ) )
                        sconscripts.extend( sub_sconscripts )
                else:
                    sconscripts.append( project )

            for toolchain in toolchains:
                toolchain_env = default_env.Clone()
                toolchain.initialise_env( toolchain_env )
                variants = self.create_build_variants( toolchain, toolchain_env )
                for variant, env in variants.items():
                    for sconscript in sconscripts:
                        self.call_project_sconscript_files( toolchain.name(), variant, env, sconscript )

            for project_generator in env[ self.project_generators_key ].itervalues():
                for sconscript in sconscripts:
                    project_generator.write( sconscript )

        else:
            print "cuppa: No projects to build. Nothing to be done"


    def call_project_sconscript_files( self, toolchain, variant, env, project ):

        sconscript_file = project
        if not os.path.exists( project ) or os.path.isdir( project ):
            sconscript_file = sconscript_file + '.sconscript'

        if os.path.exists( sconscript_file ) and os.path.isfile( sconscript_file ):

            print "cuppa: project exists and added to build [{}]".format( self._as_notice( sconscript_file ) )

            path_without_ext = os.path.splitext( sconscript_file )[0]

            sconstruct_offset_path, sconscript_name = os.path.split( sconscript_file )

            name = os.path.splitext( sconscript_name )[0]
            if name.lower() == "sconscript":
                path_without_ext = sconstruct_offset_path
                name = path_without_ext

            build_root = env['build_root']
            cloned_env = env.Clone()

            cloned_env['sconscript_file'] = sconscript_file
            cloned_env['sconscript_build_dir'] = path_without_ext
            cloned_env['sconscript_toolchain_build_dir'] = os.path.join( path_without_ext, toolchain )
            cloned_env['sconscript_dir']  = os.path.join( env['base_path'], sconstruct_offset_path )
            cloned_env['build_dir']       = os.path.normpath( os.path.join( build_root, path_without_ext, toolchain, variant, 'working', '' ) )
            cloned_env['offset_dir']      = sconstruct_offset_path
            cloned_env['final_dir']       = '..' + os.path.sep + 'final' + os.path.sep

            cloned_env.AppendUnique( INCPATH = [ cloned_env['build_dir'] ] )

            sconscript_exports = {
                'env'                     : cloned_env,
                'variant_env'             : env,
                'build_root'              : build_root,
                'build_dir'               : cloned_env['build_dir'],
                'final_dir'               : cloned_env['final_dir'],
                'common_variant_final_dir': '../../common/final/',
                'common_project_final_dir': build_root + '/common/final/',
                'project'                 : name,
            }

            cuppa.modules.registration.init_env_for_variant( "methods", sconscript_exports )

            self._configure.configure( sconscript_exports['env'] )

            SCons.Script.SConscript(
                [ sconscript_file ],
                variant_dir = sconscript_exports['build_dir'],
                duplicate   = 0,
                exports     = sconscript_exports
            )

            for project_generator in env[ self.project_generators_key ].itervalues():
                project_generator.update( variant, env, project, build_root, cloned_env['build_dir'], '../final/' )

        else:
            print "cuppa: Skipping non-existent project [{}]".format( self._as_error( sconscript_file ) )



def run( *args, **kwargs ):
    Construct( *args, **kwargs )

