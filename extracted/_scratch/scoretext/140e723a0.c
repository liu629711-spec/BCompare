function: FUN_140e723a0
entry: 140e723a0
body_size: 508
signature: undefined FUN_140e723a0()


void FUN_140e723a0(longlong param_1,byte param_2,uint param_3,longlong *param_4)

{
  longlong *plVar1;
  undefined1 auStack_78 [40];
  longlong local_50;
  ulonglong local_48;
  undefined8 local_40;
  undefined8 local_38;
  undefined1 *local_30;
  uint local_1c;
  
  local_30 = auStack_78;
  local_40 = 0;
  local_38 = 0;
  local_1c = param_3 & *(uint *)(*(longlong *)(param_1 + 0xb0) + 0x38);
  local_48 = (ulonglong)param_2;
  local_50 = (longlong)(int)local_1c;
  if (*(uint *)(*(longlong *)(*(longlong *)(param_1 + 0xb0) + 0x48 + local_48 * 8) + local_50 * 0x10
               ) == param_3) {
    local_30 = auStack_78;
    FUN_140014610(param_4,*(undefined8 *)
                           (*(longlong *)
                             (*(longlong *)(param_1 + 0xb0) + 0x48 + (ulonglong)param_2 * 8) + 8 +
                           local_50 * 0x10));
  }
  else {
    plVar1 = *(longlong **)(*(longlong *)(param_1 + 0xb0) + 0x10);
    (**(code **)(*plVar1 + 0x50))(plVar1);
    FUN_140e71cd0(*(undefined8 *)(*(longlong *)(param_1 + 0xb0) + 0x10),&local_38,param_2,param_3);
    FUN_140015490(param_4,local_38,0xfde9);
    if (*param_4 == 0) {
      plVar1 = *(longlong **)(*(longlong *)(param_1 + 0xb0) + 0x10);
      (**(code **)(*plVar1 + 0x40))(plVar1,&local_40,param_2,param_3);
      FUN_140015490(param_4,local_40,0xfde9);
    }
    *(uint *)(*(longlong *)(*(longlong *)(param_1 + 0xb0) + 0x48 + local_48 * 8) + local_50 * 0x10)
         = param_3;
    FUN_140014610(*(longlong *)(*(longlong *)(param_1 + 0xb0) + 0x48 + local_48 * 8) + 8 +
                  local_50 * 0x10,*param_4);
    plVar1 = *(longlong **)(*(longlong *)(param_1 + 0xb0) + 0x10);
    (**(code **)(*plVar1 + 0x58))(plVar1);
  }
  FUN_140013f10(&local_40,2);
  return;
}


