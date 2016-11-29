*** Settings ***

Documentation   This testsuite is for testing boot policy function.

Resource           ../lib/rest_client.robot
Resource           ../lib/ipmi_client.robot
Resource           ../lib/utils.robot
Resource           ../lib/openbmc_ffdc.robot

Suite Setup        Open Connection And Log In
Suite Teardown     Close All Connections
Test Setup         Initialize DBUS cmd   "boot_policy"
Test Teardown      FFDC On Test Case Fail

*** Variables ***

*** Test Cases ***

Set Onetime boot policy using REST
    [Documentation]   This testcase is to set onetime boot policy using REST
    ...               URI and then verify using REST API and ipmitool.\n

    Set Boot Policy   ONETIME

    ${boot}=   Read Attribute  /org/openbmc/settings/host0    boot_policy
    Should Be Equal    ${boot}    ONETIME
    ${output}   ${stderr}=  Execute Command  ${dbuscmd}  return_stderr=True
    Should Be Empty     ${stderr}
    Should Contain   ${output}    ONETIME

Set Permanent boot policy using REST
    [Documentation]   This testcase is to set permanent boot policy using REST
    ...               URI and then verify using REST API and ipmitool.\n

    Set Boot Policy   PERMANENT

    ${boot}=   Read Attribute  /org/openbmc/settings/host0    boot_policy
    Should Be Equal    ${boot}    PERMANENT
    ${output}   ${stderr}=  Execute Command  ${dbuscmd}  return_stderr=True
    Should Be Empty     ${stderr}
    Should Contain   ${output}     PERMANENT

Set Onetime boot policy using IPMITOOL
    [Documentation]   This testcase is to set boot policy to onetime boot using ipmitool
    ...               and then verify using REST URI and ipmitool.\n

    Run IPMI command   0x0 0x8 0x05 0x80 0x00 0x00 0x00 0x00
    ${boot}=   Read Attribute  /org/openbmc/settings/host0    boot_policy
    Should Be Equal    ${boot}    ONETIME
    ${output}   ${stderr}=  Execute Command  ${dbuscmd}  return_stderr=True
    Should Be Empty     ${stderr}
    Should Contain   ${output}    ONETIME

Set Permanent boot policy using IPMITOOL
    [Documentation]   This testcase is to set boot policy to permanent using ipmitool
    ...               and then verify using REST URI and ipmitool.

    Run IPMI command   0x0 0x8 0x05 0xC0 0x00 0x00 0x00 0x00
    ${boot}=   Read Attribute  /org/openbmc/settings/host0    boot_policy
    Should Be Equal    ${boot}    PERMANENT
    ${output}   ${stderr}=  Execute Command  ${dbuscmd}  return_stderr=True
    Should Be Empty     ${stderr}
    Should Contain   ${output}     PERMANENT

Boot order with permanent boot policy
    [Documentation]   This testcase is to verify that boot order does not change
    ...               after first boot when boot policy set to permanent
    [Tags]  chassisboot

    Initiate Power Off

    Set Boot Policy   PERMANENT

    Set Boot Device   CDROM

    Initiate Power On

    ${boot}=   Read Attribute  /org/openbmc/settings/host0    boot_policy
    Should Be Equal    ${boot}    PERMANENT

    ${flag}=   Read Attribute  /org/openbmc/settings/host0    boot_flags
    Should Be Equal    ${flag}    CDROM

Persist ONETIME Boot Policy After Reset
    [Documentation]   Verify ONETIME boot policy order does not change
    ...               on warm reset.
    [Tags]  chassisboot   Persist_ONETIME Boot_Policy_After_Reset

    Initiate Power On

    Set Boot Policy   ONETIME

    Set Boot Device   Network

    Trigger Warm Reset

    ${boot}=   Read Attribute  /org/openbmc/settings/host0    boot_policy
    Should Be Equal    ${boot}    ONETIME

    ${flag}=   Read Attribute  /org/openbmc/settings/host0    boot_flags
    Should Be Equal    ${flag}    Network

Persist PERMANENT Boot Policy After Reset
    [Documentation]   Verify PERMANENT boot policy order does not change
    ...               on warm reset.
    [Tags]  chassisboot    Persist_PERMANENT_Boot_Policy_After_Reset

    Initiate Power On

    Set Boot Policy   PERMANENT

    Set Boot Device   CDROM

    Trigger Warm Reset

    ${boot}=   Read Attribute  /org/openbmc/settings/host0    boot_policy
    Should Be Equal    ${boot}    PERMANENT

    ${flag}=   Read Attribute  /org/openbmc/settings/host0    boot_flags
    Should Be Equal    ${flag}    CDROM

Set boot policy to invalid value
    [Documentation]   This testcase verify that the boot policy doesn't get
    ...               updated with invalid policy supplied by user.
    [Tags]  Set_boot_policy_to_invalid_value

    Run Keyword and Ignore Error    Set Boot Policy   abc

    ${boot}=   Read Attribute  /org/openbmc/settings/host0    boot_policy
    Should Not Be Equal    ${boot}    abc

*** Keywords ***

Set Boot Policy
    [Arguments]    ${args}
    ${bootpolicy}=   Set Variable   ${args}
    ${valueDict}=   create dictionary   data=${bootpolicy}
    Write Attribute    /org/openbmc/settings/host0   boot_policy   data=${valueDict}

Set Boot Device
    [Arguments]    ${args}
    ${bootDevice}=   Set Variable   ${args}
    ${valueDict}=   create dictionary   data=${bootDevice}
    Write Attribute    /org/openbmc/settings/host0   boot_flags   data=${valueDict}



