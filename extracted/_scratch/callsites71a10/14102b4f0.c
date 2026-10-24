function: FUN_14102b4f0
entry: 14102b4f0
body_size: 325
signature: undefined FUN_14102b4f0()


void FUN_14102b4f0(longlong *param_1,longlong param_2)

{
  ulonglong uVar1;
  undefined1 auStack_98 [32];
  undefined4 local_78;
  undefined4 local_70;
  undefined4 local_68;
  byte local_51;
  code *local_50;
  longlong *local_48;
  undefined1 *local_40;
  byte local_29;
  undefined4 local_28;
  undefined4 local_24;
  undefined8 local_20;
  
  local_40 = auStack_98;
  local_51 = *(byte *)(param_2 + 0x90);
  local_78 = CONCAT31(local_78._1_3_,local_51);
  local_29 = local_51;
  local_20 = FUN_14102c200(PTR_LAB_141020f20,1,param_1[0x1d],2);
  (**(code **)(*param_1 + 0x90))(param_1,local_51,&local_24,&local_28);
  local_50 = FUN_14102aad0;
  uVar1 = (ulonglong)local_29;
  local_78 = *(undefined4 *)((longlong)param_1 + uVar1 * 4 + 0x138);
  local_70 = local_28;
  local_68 = *(undefined4 *)((longlong)param_1 + uVar1 * 4 + 0x140);
  local_48 = param_1;
  FUN_140e71a10(local_20,param_2,&local_50,local_24);
  *(undefined1 *)((longlong)param_1 + uVar1 + 0x120) = 1;
  if (*(char *)((longlong)param_1 + (ulonglong)(byte)PTR_DAT_141fb2d98[uVar1] + 0x120) != '\0') {
    (**(code **)(*param_1 + 0x88))(param_1,param_2);
  }
  FUN_140010870(local_20);
  return;
}


