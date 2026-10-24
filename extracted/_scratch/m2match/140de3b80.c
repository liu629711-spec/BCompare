function: FUN_140de3b80
entry: 140de3b80
body_size: 71
signature: undefined FUN_140de3b80()


void FUN_140de3b80(longlong param_1,undefined8 *param_2,undefined8 param_3,undefined4 *param_4)

{
  char cVar1;
  
  cVar1 = FUN_140dc5d80(*(undefined8 *)(param_1 + 0x10),*param_2,param_2[1],*param_4,param_4[1]);
  if (cVar1 == '\0') {
    FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Bc\\BcAlign.pas",0x1d9);
  }
  return;
}


