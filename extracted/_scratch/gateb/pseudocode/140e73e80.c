function: FUN_140e73e80
entry: 140e73e80
body_size: 166
signature: undefined FUN_140e73e80()


int FUN_140e73e80(longlong param_1,int param_2,int param_3)

{
  int iVar1;
  longlong lVar2;
  longlong lVar3;
  
  lVar3 = (longlong)param_3;
  lVar2 = (longlong)param_2;
  iVar1 = *(int *)(*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + 4 + lVar3 * 0x10) -
          *(int *)(*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + 4 + lVar2 * 0x10);
  if ((iVar1 == 0) &&
     (iVar1 = *(int *)(*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + 0xc + lVar2 * 0x10) -
              *(int *)(*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + 0xc + lVar3 * 0x10),
     iVar1 == 0)) {
    iVar1 = *(int *)(*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + 8 + lVar2 * 0x10) -
            *(int *)(*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + 8 + lVar3 * 0x10);
  }
  return iVar1;
}


