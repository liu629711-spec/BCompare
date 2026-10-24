function: FUN_140e72330
entry: 140e72330
body_size: 102
signature: undefined FUN_140e72330()


void FUN_140e72330(longlong param_1,int param_2)

{
  longlong lVar1;
  
  lVar1 = (longlong)param_2;
  if (*(longlong *)(*(longlong *)(param_1 + 0xa0) + lVar1 * 8) == 0) {
    FUN_140019870(*(longlong *)(param_1 + 0xa0) + lVar1 * 8,PTR_DAT_140e71438,1,
                  (longlong)(*(int *)(param_1 + 0x5c) + 1));
    FUN_14000dce0(*(undefined8 *)(*(longlong *)(param_1 + 0xa0) + lVar1 * 8),
                  (longlong)*(int *)(param_1 + 0x5c),0);
  }
  return;
}


