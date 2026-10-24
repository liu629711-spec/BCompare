function: FUN_140b3a7b0
entry: 140b3a7b0
body_size: 323
signature: undefined FUN_140b3a7b0()


longlong FUN_140b3a7b0(longlong param_1,char param_2,undefined8 param_3)

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
  FUN_140ae2fd0(local_res8,0,param_3);
  *(undefined1 *)(local_res8 + 0x98) = 1;
  FUN_1400144c0(local_res8 + 0xb0,*(undefined8 *)PTR_DAT_141faf2a0);
  *(undefined1 *)(local_res8 + 0x99) = 0;
  *(undefined1 *)(local_res8 + 0x9a) = 1;
  *(undefined1 *)(local_res8 + 0x9b) = 2;
  *(undefined1 *)(local_res8 + 0x9c) = 0;
  *(undefined8 *)(local_res8 + 0xa8) = 0;
  *(undefined1 *)(local_res8 + 0xe1) = 0;
  *(undefined8 *)(local_res8 + 0xb8) = 0;
  FUN_140019a50(local_res8 + 0xc0,PTR_DAT_1406e61b0);
  *(undefined8 *)(local_res8 + 200) = 0;
  *(undefined1 *)(local_res8 + 0xe0) = 0;
  *(undefined8 *)(local_res8 + 0xa0) = 0;
  *(undefined1 *)(local_res8 + 0xe2) = 0;
  *(undefined8 *)(local_res8 + 0xd0) = 0;
  *(undefined8 *)(local_res8 + 0xd8) = 0;
  if (param_2 != '\0') {
    local_res8 = FUN_1400112a0(local_res8);
  }
  return local_res8;
}


