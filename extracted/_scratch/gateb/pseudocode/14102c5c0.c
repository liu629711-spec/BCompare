function: FUN_14102c5c0
entry: 14102c5c0
body_size: 138
signature: undefined FUN_14102c5c0()


longlong FUN_14102c5c0(longlong param_1,char param_2,undefined8 param_3,undefined4 param_4,
                      undefined1 param_5)

{
  undefined1 *puVar1;
  undefined8 uVar2;
  longlong local_res8;
  undefined1 auStack_48 [40];
  undefined1 *local_20;
  
  local_20 = auStack_48;
  local_res8 = param_1;
  puVar1 = auStack_48;
  if (param_2 != '\0') {
    local_res8 = FUN_140011260(param_1,param_2);
    puVar1 = local_20;
  }
  local_20 = puVar1;
  FUN_14102c500(local_res8,0,param_3,param_4);
  uVar2 = FUN_141028aa0(*(undefined8 *)(local_res8 + 0x10),param_5);
  *(undefined8 *)(local_res8 + 0x20) = uVar2;
  if (param_2 != '\0') {
    local_res8 = FUN_1400112a0(local_res8);
  }
  return local_res8;
}


