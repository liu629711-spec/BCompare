function: FUN_140e722a0
entry: 140e722a0
body_size: 132
signature: undefined FUN_140e722a0()


void FUN_140e722a0(longlong param_1,uint param_2,int param_3,int *param_4)

{
  bool bVar1;
  int iVar2;
  ulonglong uVar3;
  
  uVar3 = (ulonglong)param_2;
  if ((*param_4 < param_3) || (*(int *)(param_1 + 0x20 + (uVar3 & 0xff) * 4) < param_3)) {
    bVar1 = false;
  }
  else {
    bVar1 = true;
  }
  if ((bVar1) && (*(int *)(param_1 + 0x3c + (uVar3 & 0xff) * 4) < param_3)) {
    FUN_140e72af0(param_1,uVar3,param_3);
    iVar2 = *(int *)(param_1 + 0x20 + (uVar3 & 0xff) * 4);
    if ((iVar2 == 0x7ffffffd) || (param_3 <= iVar2)) {
      bVar1 = true;
    }
    else {
      bVar1 = false;
    }
  }
  if (!bVar1) {
    iVar2 = *(int *)(param_1 + 0x20 + (uVar3 & 0xff) * 4);
    if (*param_4 <= iVar2) {
      iVar2 = *param_4;
    }
    *param_4 = iVar2;
  }
  return;
}


