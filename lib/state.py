#!/usr/bin/env python

r"""
This module contains functions having to do with machine state: get_state,
check_state, wait_state, etc.

The 'State' is a composite of many pieces of data.  Therefore, the functions
in this module define state as an ordered dictionary.  Here is an example of
some test output showing machine state:

state:
  state[power]:                                   1
  state[bmc]:                                     HOST_BOOTED
  state[boot_progress]:                           FW Progress, Starting OS
  state[os_ping]:                                 1
  state[os_login]:                                1
  state[os_run_cmd]:                              1

Different users may very well have different needs when inquiring about
state.  In the future, we can add code to allow a user to specify which
pieces of info they need in the state dictionary.  Examples of such data
might include uptime, state timestamps, boot side, etc.

By using the wait_state function, a caller can start a boot and then wait for
a precisely defined state to indicate that the boot has succeeded.  If
the boot fails, they can see exactly why by looking at the current state as
compared with the expected state.
"""

import gen_print as gp
import gen_robot_print as grp
import gen_valid as gv

import commands
from robot.libraries.BuiltIn import BuiltIn

import re

# We need utils.robot to get keywords like "Get Power State".
BuiltIn().import_resource("utils.robot")


###############################################################################
def anchor_state(state):

    r"""
    Add regular expression anchors ("^" and "$") to the beginning and end of
    each item in the state dictionary passed in.  Return the resulting
    dictionary.

    Description of Arguments:
    state    A dictionary such as the one returned by the get_state()
             function.
    """

    anchored_state = state
    for key, match_state_value in anchored_state.items():
        anchored_state[key] = "^" + str(anchored_state[key]) + "$"

    return anchored_state

###############################################################################


###############################################################################
def compare_states(state,
                   match_state):

    r"""
    Compare 2 state dictionaries.  Return True if the match and False if they
    don't.  Note that the match_state dictionary does not need to have an entry
    corresponding to each entry in the state dictionary.  But for each entry
    that it does have, the corresponding state entry will be checked for a
    match.

    Description of arguments:
    state           A state dictionary such as the one returned by the
                    get_state function.
    match_state     A dictionary whose key/value pairs are "state field"/
                    "state value".  The state value is interpreted as a
                    regular expression.  Every value in this dictionary is
                    considered.  If each and every one matches, the 2
                    dictionaries are considered to be matching.
    """

    match = True
    for key, match_state_value in match_state.items():
        try:
            if not re.match(match_state_value, str(state[key])):
                match = False
                break
        except KeyError:
            match = False
            break

    return match

###############################################################################


###############################################################################
def get_os_state(os_host="",
                 os_username="",
                 os_password="",
                 quiet=None):

    r"""
    Get component states for the operating system such as ping, login,
    etc, put them into a dictionary and return them to the caller.

    Description of arguments:
    os_host      The DNS name or IP address of the operating system.
                 This defaults to global ${OS_HOST}.
    os_username  The username to be used to login to the OS.
                 This defaults to global ${OS_USERNAME}.
    os_password  The password to be used to login to the OS.
                 This defaults to global ${OS_PASSWORD}.
    quiet        Indicates whether status details (e.g. curl commands) should
                 be written to the console.
                 Defaults to either global value of ${QUIET} or to 1.
    """

    quiet = grp.set_quiet_default(quiet, 1)

    # Set parm defaults where necessary and validate all parms.
    if os_host == "":
        os_host = BuiltIn().get_variable_value("${OS_HOST}")
    error_message = gv.svalid_value(os_host, var_name="os_host",
                                    invalid_values=[None, ""])
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    if os_username == "":
        os_username = BuiltIn().get_variable_value("${OS_USERNAME}")
    error_message = gv.svalid_value(os_username, var_name="os_username",
                                    invalid_values=[None, ""])
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    if os_password == "":
        os_password = BuiltIn().get_variable_value("${OS_PASSWORD}")
    error_message = gv.svalid_value(os_password, var_name="os_password",
                                    invalid_values=[None, ""])
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    # See if the OS pings.
    cmd_buf = "ping -c 1 -w 2 " + os_host
    if not quiet:
        grp.rpissuing(cmd_buf)
    rc, out_buf = commands.getstatusoutput(cmd_buf)
    if rc == 0:
        pings = 1
    else:
        pings = 0

    # Open SSH connection to OS.
    cmd_buf = ["Open Connection", os_host]
    if not quiet:
        grp.rpissuing_keyword(cmd_buf)
    ix = BuiltIn().run_keyword(*cmd_buf)

    # Login to OS.
    cmd_buf = ["Login", os_username, os_password]
    if not quiet:
        grp.rpissuing_keyword(cmd_buf)
    status, msg = BuiltIn().run_keyword_and_ignore_error(*cmd_buf)

    if status == "PASS":
        login = 1
    else:
        login = 0

    if login:
        # Try running a simple command (uptime) on the OS.
        cmd_buf = ["Execute Command", "uptime", "return_stderr=True",
                   "return_rc=True"]
        if not quiet:
            grp.rpissuing_keyword(cmd_buf)
        output, stderr_buf, rc = BuiltIn().run_keyword(*cmd_buf)
        if rc == 0 and stderr_buf == "":
            run_cmd = 1
        else:
            run_cmd = 0
    else:
        run_cmd = 0

    # Create a dictionary containing the results of the prior commands.
    cmd_buf = ["Create Dictionary", "ping=${" + str(pings) + "}",
               "login=${" + str(login) + "}",
               "run_cmd=${" + str(run_cmd) + "}"]
    grp.rdpissuing_keyword(cmd_buf)
    os_state = BuiltIn().run_keyword(*cmd_buf)

    return os_state

###############################################################################


###############################################################################
def get_state(openbmc_host="",
              openbmc_username="",
              openbmc_password="",
              os_host="",
              os_username="",
              os_password="",
              quiet=None):

    r"""
    Get component states such as power state, bmc state, etc, put them into a
    dictionary and return them to the caller.

    Description of arguments:
    openbmc_host      The DNS name or IP address of the BMC.
                      This defaults to global ${OPENBMC_HOST}.
    openbmc_username  The username to be used to login to the BMC.
                      This defaults to global ${OPENBMC_USERNAME}.
    openbmc_password  The password to be used to login to the BMC.
                      This defaults to global ${OPENBMC_PASSWORD}.
    os_host           The DNS name or IP address of the operating system.
                      This defaults to global ${OS_HOST}.
    os_username       The username to be used to login to the OS.
                      This defaults to global ${OS_USERNAME}.
    os_password       The password to be used to login to the OS.
                      This defaults to global ${OS_PASSWORD}.
    quiet             Indicates whether status details (e.g. curl commands)
                      should be written to the console.
                      Defaults to either global value of ${QUIET} or to 1.
    """

    quiet = grp.set_quiet_default(quiet, 1)

    # Set parm defaults where necessary and validate all parms.
    if openbmc_host == "":
        openbmc_host = BuiltIn().get_variable_value("${OPENBMC_HOST}")
    error_message = gv.svalid_value(openbmc_host,
                                    var_name="openbmc_host",
                                    invalid_values=[None, ""])
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    if openbmc_username == "":
        openbmc_username = BuiltIn().get_variable_value("${OPENBMC_USERNAME}")
    error_message = gv.svalid_value(openbmc_username,
                                    var_name="openbmc_username",
                                    invalid_values=[None, ""])
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    if openbmc_password == "":
        openbmc_password = BuiltIn().get_variable_value("${OPENBMC_PASSWORD}")
    error_message = gv.svalid_value(openbmc_password,
                                    var_name="openbmc_password",
                                    invalid_values=[None, ""])
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    # Set parm defaults where necessary and validate all parms.  NOTE: OS parms
    # are optional.
    if os_host == "":
        os_host = BuiltIn().get_variable_value("${OS_HOST}")
        if os_host is None:
            os_host = ""

    if os_username is "":
        os_username = BuiltIn().get_variable_value("${OS_USERNAME}")
        if os_username is None:
            os_username = ""

    if os_password is "":
        os_password = BuiltIn().get_variable_value("${OS_PASSWORD}")
        if os_password is None:
            os_password = ""

    # Get the component states.
    cmd_buf = ["Get Power State", "quiet=${" + str(quiet) + "}"]
    grp.rdpissuing_keyword(cmd_buf)
    power = BuiltIn().run_keyword(*cmd_buf)

    cmd_buf = ["Get BMC State", "quiet=${" + str(quiet) + "}"]
    grp.rdpissuing_keyword(cmd_buf)
    bmc = BuiltIn().run_keyword(*cmd_buf)

    cmd_buf = ["Get Boot Progress", "quiet=${" + str(quiet) + "}"]
    grp.rdpissuing_keyword(cmd_buf)
    boot_progress = BuiltIn().run_keyword(*cmd_buf)

    # Create composite state dictionary.
    cmd_buf = ["Create Dictionary", "power=${" + str(power) + "}",
               "bmc=" + bmc, "boot_progress=" + boot_progress]
    grp.rdpissuing_keyword(cmd_buf)
    state = BuiltIn().run_keyword(*cmd_buf)

    if os_host != "":
        # Create an os_up_match dictionary to test whether we are booted enough
        # to get operating system info.
        cmd_buf = ["Create Dictionary", "power=^${1}$", "bmc=^HOST_BOOTED$",
                   "boot_progress=^FW Progress, Starting OS$"]
        grp.rdpissuing_keyword(cmd_buf)
        os_up_match = BuiltIn().run_keyword(*cmd_buf)
        os_up = compare_states(state, os_up_match)

        if os_up:
            # Get OS information...
            os_state = get_os_state(os_host=os_host,
                                    os_username=os_username,
                                    os_password=os_password,
                                    quiet=quiet)
            for key, state_value in os_state.items():
                # Add each OS value to the state dictionary, pre-pending
                # "os_" to each key.
                new_key = "os_" + key
                state[new_key] = state_value

    return state

###############################################################################


###############################################################################
def check_state(match_state,
                invert=0,
                print_string="",
                openbmc_host="",
                openbmc_username="",
                openbmc_password="",
                os_host="",
                os_username="",
                os_password="",
                quiet=None):

    r"""
    Check that the Open BMC machine's composite state matches the specified
    state.  On success, this keyword returns the machine's composite state as a
    dictionary.

    Description of arguments:
    match_state       A dictionary whose key/value pairs are "state field"/
                      "state value".  The state value is interpreted as a
                      regular expression.  Example call from robot:
                      ${match_state}=  Create Dictionary  power=^1$
                      ...  bmc=^HOST_BOOTED$
                      ...  boot_progress=^FW Progress, Starting OS$
                      ${state}=  Check State  &{match_state}
    invert            If this flag is set, this function will succeed if the
                      states do NOT match.
    print_string      This function will print this string to the console prior
                      to getting the state.
    openbmc_host      The DNS name or IP address of the BMC.
                      This defaults to global ${OPENBMC_HOST}.
    openbmc_username  The username to be used to login to the BMC.
                      This defaults to global ${OPENBMC_USERNAME}.
    openbmc_password  The password to be used to login to the BMC.
                      This defaults to global ${OPENBMC_PASSWORD}.
    os_host           The DNS name or IP address of the operating system.
                      This defaults to global ${OS_HOST}.
    os_username       The username to be used to login to the OS.
                      This defaults to global ${OS_USERNAME}.
    os_password       The password to be used to login to the OS.
                      This defaults to global ${OS_PASSWORD}.
    quiet             Indicates whether status details should be written to the
                      console.  Defaults to either global value of ${QUIET} or
                      to 1.
    """

    quiet = grp.set_quiet_default(quiet, 1)

    grp.rprint(print_string)

    # Initialize state.
    state = get_state(openbmc_host=openbmc_host,
                      openbmc_username=openbmc_username,
                      openbmc_password=openbmc_password,
                      os_host=os_host,
                      os_username=os_username,
                      os_password=os_password,
                      quiet=quiet)
    if not quiet:
        grp.rprint_var(state)

    match = compare_states(state, match_state)

    if invert and match:
        fail_msg = "The current state of the machine matches the match" +\
                   " state:\n" + gp.sprint_varx("state", state)
        BuiltIn().fail("\n" + gp.sprint_error(fail_msg))
    elif not invert and not match:
        fail_msg = "The current state of the machine does NOT match the" +\
                   " match state:\n" +\
                   gp.sprint_varx("state", state)
        BuiltIn().fail("\n" + gp.sprint_error(fail_msg))

    return state

###############################################################################


###############################################################################
def wait_state(match_state,
               wait_time="1 min",
               interval="1 second",
               invert=0,
               openbmc_host="",
               openbmc_username="",
               openbmc_password="",
               os_host="",
               os_username="",
               os_password="",
               quiet=None):

    r"""
    Wait for the Open BMC machine's composite state to match the specified
    state.  On success, this keyword returns the machine's composite state as
    a dictionary.

    Description of arguments:
    match_state       A dictionary whose key/value pairs are "state field"/
                      "state value".  See check_state (above) for details.
    wait_time         The total amount of time to wait for the desired state.
                      This value may be expressed in Robot Framework's time
                      format (e.g. 1 minute, 2 min 3 s, 4.5).
    interval          The amount of time between state checks.
                      This value may be expressed in Robot Framework's time
                      format (e.g. 1 minute, 2 min 3 s, 4.5).
    invert            If this flag is set, this function will for the state of
                      the machine to cease to match the match state.
    openbmc_host      The DNS name or IP address of the BMC.
                      This defaults to global ${OPENBMC_HOST}.
    openbmc_username  The username to be used to login to the BMC.
                      This defaults to global ${OPENBMC_USERNAME}.
    openbmc_password  The password to be used to login to the BMC.
                      This defaults to global ${OPENBMC_PASSWORD}.
    os_host           The DNS name or IP address of the operating system.
                      This defaults to global ${OS_HOST}.
    os_username       The username to be used to login to the OS.
                      This defaults to global ${OS_USERNAME}.
    os_password       The password to be used to login to the OS.
                      This defaults to global ${OS_PASSWORD}.
    quiet             Indicates whether status details should be written to the
                      console.  Defaults to either global value of ${QUIET} or
                      to 1.
    """

    quiet = grp.set_quiet_default(quiet, 1)

    if not quiet:
        if invert:
            alt_text = "cease to "
        else:
            alt_text = ""
        grp.rprint_timen("Checking every " + str(interval) + " for up to " +
                         str(wait_time) + " for the state of the machine to " +
                         alt_text + "match the state shown below.")
        grp.rprint_var(match_state)

    cmd_buf = ["Check State", match_state, "invert=${" + str(invert) + "}",
               "print_string=#", "openbmc_host=" + openbmc_host,
               "openbmc_username=" + openbmc_username,
               "openbmc_password=" + openbmc_password, "os_host=" + os_host,
               "os_username=" + os_username, "os_password=" + os_password,
               "quiet=${1}"]
    grp.rdpissuing_keyword(cmd_buf)
    state = BuiltIn().wait_until_keyword_succeeds(wait_time, interval,
                                                  *cmd_buf)

    if not quiet:
        grp.rprintn()
        if invert:
            grp.rprint_timen("The states no longer match:")
        else:
            grp.rprint_timen("The states match:")
        grp.rprint_var(state)

    return state

###############################################################################