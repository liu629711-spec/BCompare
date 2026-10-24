function: FUN_140b25740
entry: 140b25740
body_size: 700
signature: undefined FUN_140b25740()


longlong FUN_140b25740(longlong param_1,char param_2,undefined8 param_3)

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
  FUN_14014d280(local_res8,0,param_3);
  *(undefined8 *)(local_res8 + 0x110) = 0;
  *(undefined8 *)(local_res8 + 0x118) = 0;
  uVar2 = FUN_140845660(PTR_PTR_1408427f8,1,0);
  *(undefined8 *)(local_res8 + 0x120) = uVar2;
  uVar2 = FUN_140835240(PTR_LAB_140834618,1,0);
  *(undefined8 *)(local_res8 + 0x128) = uVar2;
  uVar2 = FUN_1408927d0(PTR_PTR_1408924b0,1);
  *(undefined8 *)(local_res8 + 0x130) = uVar2;
  *(undefined1 *)(local_res8 + 0x138) = 0;
  uVar2 = FUN_1400107b0(PTR_PTR_1400e9f60,1);
  *(undefined8 *)(local_res8 + 0x140) = uVar2;
  uVar2 = FUN_1400107b0(PTR_PTR_1400e9f60,1);
  *(undefined8 *)(local_res8 + 0x148) = uVar2;
  FUN_140019a50(local_res8 + 0x150,PTR_DAT_1406e6478);
  uVar2 = FUN_1406b2b90();
  *(undefined8 *)(local_res8 + 0x158) = uVar2;
  *(undefined1 *)(local_res8 + 0x160) = 1;
  *(undefined1 *)(local_res8 + 0x161) = 0;
  *(undefined1 *)(local_res8 + 0x10c) = 0;
  *(undefined4 *)(local_res8 + 0x108) = 0;
  *(undefined1 *)(local_res8 + 0x10d) = 1;
  *(undefined1 *)(local_res8 + 0x80) = DAT_140b25a40;
  *(undefined1 *)(local_res8 + 0x81) = DAT_140b25a40;
  uVar2 = FUN_1406b2b90();
  *(undefined8 *)(local_res8 + 0xb0) = uVar2;
  *(undefined1 *)(local_res8 + 0xda) = 0;
  *(undefined1 *)(local_res8 + 0xd9) = 0;
  *(undefined8 *)(local_res8 + 0x168) = 0;
  *(undefined8 *)(local_res8 + 0x88) = 0;
  *(undefined8 *)(local_res8 + 0x90) = 0;
  *(undefined8 *)(local_res8 + 0x98) = 0;
  *(undefined8 *)(local_res8 + 0xa0) = 0;
  *(undefined8 *)(local_res8 + 0xa8) = 0;
  *(undefined8 *)(local_res8 + 0xb8) = 0;
  *(undefined1 *)(local_res8 + 0xc0) = 0;
  *(undefined8 *)(local_res8 + 200) = 0;
  *(undefined1 *)(local_res8 + 0xd8) = 0;
  *(undefined8 *)(local_res8 + 0xd0) = 0;
  *(undefined8 *)(local_res8 + 0xe0) = 0;
  *(undefined8 *)(local_res8 + 0xe8) = 0;
  *(undefined8 *)(local_res8 + 0xf0) = 0;
  *(undefined8 *)(local_res8 + 0xf8) = 0;
  *(undefined8 *)(local_res8 + 0x100) = 0;
  *(undefined1 *)(local_res8 + 0x170) = 4;
  *(undefined4 *)(local_res8 + 0x171) = DAT_140b25a41;
  if (param_2 != '\0') {
    local_res8 = FUN_1400112a0(local_res8);
  }
  return local_res8;
}


