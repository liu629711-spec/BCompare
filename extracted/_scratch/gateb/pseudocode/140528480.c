function: FUN_140528480
entry: 140528480
body_size: 78
signature: undefined FUN_140528480()


void FUN_140528480(longlong *param_1,int param_2,undefined4 *param_3)

{
  char cVar1;
  int local_20;
  int local_1c;
  
  cVar1 = (**(code **)(*param_1 + 8))(param_1,(longlong)param_2,&local_1c,&local_20);
  if (cVar1 != '\0') {
    *param_3 = (int)*(undefined8 *)
                     (*(longlong *)(param_1[1] + 8 + (longlong)local_1c * 0x10) + 8 +
                     (longlong)local_20 * 0x10);
  }
  return;
}


