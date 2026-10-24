function: FUN_14102a820
entry: 14102a820
body_size: 299
signature: undefined FUN_14102a820()


void FUN_14102a820(longlong param_1,undefined8 param_2,int param_3,int param_4,int param_5)

{
  int iVar1;
  longlong lVar2;
  int local_24;
  int local_20;
  
  local_20 = param_4;
  local_24 = param_3;
  do {
    if (param_5 < 1) {
      return;
    }
    if (((*(char *)(param_1 + 0xf0) != '\0') && (-1 < local_24)) && (-1 < local_20)) {
      while (*(int *)(param_1 + 0xf4) <= *(int *)(param_1 + 0x118)) {
        iVar1 = FUN_141028b00(*(undefined8 *)(param_1 + 0xe8),0,*(undefined4 *)(param_1 + 0xf4));
        if ((local_24 <= iVar1) &&
           (iVar1 = FUN_141028b00(*(undefined8 *)(param_1 + 0xe8),1,*(undefined4 *)(param_1 + 0xf4))
           , local_20 <= iVar1)) break;
        *(int *)(param_1 + 0xf4) = *(int *)(param_1 + 0xf4) + 1;
      }
      if (*(int *)(param_1 + 0xf4) <= *(int *)(param_1 + 0x118)) {
        iVar1 = FUN_141028b00(*(undefined8 *)(param_1 + 0xe8),0,*(int *)(param_1 + 0xf4));
        if (iVar1 == local_24) {
          iVar1 = FUN_141028b00(*(undefined8 *)(param_1 + 0xe8),1,*(undefined4 *)(param_1 + 0xf4));
          if (iVar1 == local_20) {
            lVar2 = FUN_140052fe0(PTR_PTR_140e70008,1,0);
            *(undefined4 *)(lVar2 + 0x30) = *(undefined4 *)(param_1 + 0xf4);
            FUN_140012e10(lVar2);
          }
        }
      }
    }
    FUN_140ef4150(*(undefined8 *)(param_1 + 0xf8));
    if (-1 < local_24) {
      local_24 = local_24 + 1;
    }
    if (-1 < local_20) {
      local_20 = local_20 + 1;
    }
    param_5 = param_5 + -1;
  } while( true );
}


