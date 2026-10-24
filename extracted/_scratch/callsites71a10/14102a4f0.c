function: FUN_14102a4f0
entry: 14102a4f0
body_size: 231
signature: undefined FUN_14102a4f0()


void FUN_14102a4f0(longlong param_1)

{
  undefined1 auStack_78 [32];
  undefined4 local_58;
  undefined4 local_50;
  undefined4 local_48;
  code *local_30;
  longlong local_28;
  undefined1 *local_20;
  undefined8 local_10;
  
  local_20 = auStack_78;
  FUN_140dd5230(param_1);
  if ((*(byte *)(*(longlong *)(param_1 + 0xe8) + 0x50) & 1) == 0) {
    FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",0x9a7);
  }
  local_58 = CONCAT31(local_58._1_3_,1);
  local_10 = FUN_14102c200(PTR_LAB_141020f20,1,*(undefined8 *)(param_1 + 0xe8),0);
  local_30 = FUN_14102a380;
  local_58 = 0;
  local_50 = 0xffffffff;
  local_48 = 0xffffffff;
  local_28 = param_1;
  FUN_140e71a10(local_10,param_1,&local_30,0);
  FUN_140010870(local_10);
  FUN_141022720(*(undefined8 *)(param_1 + 0xe8),param_1);
  return;
}


