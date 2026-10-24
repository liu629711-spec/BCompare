function: FUN_140b611e0
entry: 140b611e0
body_size: 241
signature: undefined FUN_140b611e0()


void FUN_140b611e0(longlong param_1,undefined8 param_2,undefined8 param_3)

{
  int iVar1;
  undefined8 uVar2;
  longlong lVar3;
  undefined1 auStack_38 [32];
  
  FUN_140b61300(param_1);
  *(undefined8 *)(param_1 + 8) = param_3;
  *(undefined8 *)(param_1 + 0x10) = param_2;
  *(undefined1 *)(param_1 + 0x39) = 1;
  uVar2 = FUN_140b3b950(PTR_PTR_140b31950,1,0);
  *(undefined8 *)(param_1 + 0x18) = uVar2;
  *(undefined1 *)(param_1 + 0x78) = 1;
  uVar2 = FUN_140b2d680(PTR_LAB_140b1d400,1,0);
  *(undefined8 *)(param_1 + 0x70) = uVar2;
  lVar3 = *(longlong *)(param_1 + 0x18);
  *(undefined8 *)(lVar3 + 0xf8) = uVar2;
  FUN_140b3baa0(lVar3,*(undefined8 *)(param_1 + 0x10));
  FUN_140ae3100(*(undefined8 *)(param_1 + 0x18),*(undefined8 *)(*(longlong *)(param_1 + 8) + 0xa8));
  iVar1 = FUN_140ad3b90(*(undefined8 *)(*(longlong *)(param_1 + 0x18) + 0xa8));
  if (0 < iVar1) {
    lVar3 = FUN_140ad3ba0(*(undefined8 *)(*(longlong *)(param_1 + 0x18) + 0xa8),0);
    *(undefined1 *)(param_1 + 0x38) = *(undefined1 *)(lVar3 + 0x10);
  }
  FUN_140b610e0(auStack_38);
  return;
}


