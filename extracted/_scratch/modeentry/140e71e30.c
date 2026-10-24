function: FUN_140e71e30
entry: 140e71e30
body_size: 99
signature: undefined FUN_140e71e30()


void FUN_140e71e30(longlong param_1,int param_2,int param_3,int param_4)

{
  longlong lVar1;
  int iVar2;
  
  FUN_140ddfb30(*(undefined8 *)(param_1 + 8));
  if (0 < param_4) {
    (**(code **)(param_1 + 0x28))
              (*(undefined8 *)(param_1 + 0x30),*(undefined8 *)(param_1 + 8),param_2,param_3,param_4)
    ;
    lVar1 = *(longlong *)(param_1 + 8);
    if (lVar1 != 0) {
      iVar2 = *(int *)(lVar1 + 0x68);
      if (-1 < param_2) {
        iVar2 = iVar2 + param_4;
      }
      if (-1 < param_3) {
        iVar2 = iVar2 + param_4;
      }
      *(longlong *)(lVar1 + 0x68) = (longlong)iVar2;
    }
  }
  return;
}


