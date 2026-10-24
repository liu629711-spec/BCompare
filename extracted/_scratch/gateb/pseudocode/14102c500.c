function: FUN_14102c500
entry: 14102c500
body_size: 118
signature: undefined FUN_14102c500()


longlong FUN_14102c500(longlong param_1,char param_2,undefined8 param_3,undefined4 param_4)

{
  undefined1 *puVar1;
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
  FUN_1400107b0(local_res8,0);
  *(undefined8 *)(local_res8 + 0x10) = param_3;
  *(undefined4 *)(local_res8 + 0x18) = param_4;
  if (param_2 != '\0') {
    local_res8 = FUN_1400112a0(local_res8);
  }
  return local_res8;
}


