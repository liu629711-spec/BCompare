function: FUN_140e73cc0
entry: 140e73cc0
body_size: 112
signature: undefined FUN_140e73cc0()


int FUN_140e73cc0(longlong param_1,int param_2,int param_3)

{
  int iVar1;
  
  iVar1 = *(int *)(*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + 0xc +
                  (longlong)param_2 * 0x10) -
          *(int *)(*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + 0xc +
                  (longlong)param_3 * 0x10);
  if (iVar1 == 0) {
    iVar1 = *(int *)(*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + 8 +
                    (longlong)param_2 * 0x10) -
            *(int *)(*(longlong *)(*(longlong *)(param_1 + 0x90) + 0x90) + 8 +
                    (longlong)param_3 * 0x10);
  }
  return iVar1;
}


