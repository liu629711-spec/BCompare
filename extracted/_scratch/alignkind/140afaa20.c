function: FUN_140afaa20
entry: 140afaa20
body_size: 182
signature: undefined FUN_140afaa20()


longlong FUN_140afaa20(longlong param_1,char param_2,undefined1 param_3,undefined8 param_4,
                      undefined1 param_5)

{
  undefined1 *puVar1;
  longlong local_res8;
  undefined1 auStack_58 [32];
  undefined1 local_38;
  undefined1 *local_20;
  
  local_20 = auStack_58;
  local_res8 = param_1;
  puVar1 = auStack_58;
  if (param_2 != '\0') {
    local_res8 = FUN_140011260(param_1,param_2);
    puVar1 = local_20;
  }
  local_20 = puVar1;
  local_38 = param_5;
  FUN_140af8f70(local_res8,0,param_3,param_4);
  FUN_1400144c0(local_res8 + 0x30,*(undefined8 *)PTR_DAT_141faf2a0);
  FUN_140019a50(local_res8 + 0x28,PTR_DAT_1406e61b0);
  *(undefined1 *)(local_res8 + 0x38) = 0;
  if (param_2 != '\0') {
    local_res8 = FUN_1400112a0(local_res8);
  }
  return local_res8;
}


