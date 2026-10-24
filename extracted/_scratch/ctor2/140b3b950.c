function: FUN_140b3b950
entry: 140b3b950
body_size: 171
signature: undefined FUN_140b3b950()


longlong FUN_140b3b950(longlong param_1,char param_2,undefined8 param_3)

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
  FUN_140b3a7b0(local_res8,0,param_3);
  *(undefined8 *)(local_res8 + 0x100) = 0;
  *(undefined1 *)(local_res8 + 0x108) = DAT_140b3ba40;
  *(undefined1 *)(local_res8 + 0x109) = 0;
  *(undefined8 *)(local_res8 + 0xf8) = 0;
  FUN_140013e30(local_res8 + 0x110);
  if (param_2 != '\0') {
    local_res8 = FUN_1400112a0(local_res8);
  }
  return local_res8;
}


