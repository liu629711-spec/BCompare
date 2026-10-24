function: FUN_141027b90
entry: 141027b90
body_size: 285
signature: undefined FUN_141027b90()


void FUN_141027b90(longlong param_1,int param_2,int param_3)

{
  byte bVar1;
  char cVar2;
  undefined4 uVar3;
  longlong *plVar4;
  undefined8 uVar5;
  char cVar6;
  ulonglong uVar7;
  int iVar8;
  
  if (param_2 <= param_3) {
    iVar8 = (param_3 - param_2) + 1;
    do {
      *(undefined1 *)(*(longlong *)(param_1 + 0x48) + 0xf + (longlong)param_2 * 0x14) = 0;
      bVar1 = 0;
      do {
        *(undefined1 *)
         (*(longlong *)(param_1 + 0x48) + 0x10 + (longlong)param_2 * 0x14 + (ulonglong)bVar1) = 0;
        bVar1 = bVar1 + 1;
      } while (bVar1 != 2);
      *(undefined1 *)(*(longlong *)(param_1 + 0x48) + 0x12 + (longlong)param_2 * 0x14) = 4;
      uVar7 = 0;
      do {
        *(undefined1 *)(*(longlong *)(param_1 + 0x48) + 0xc + (longlong)param_2 * 0x14 + uVar7) = 0;
        bVar1 = (char)uVar7 + 1;
        uVar7 = (ulonglong)bVar1;
      } while (bVar1 != 3);
      cVar6 = '\0';
      do {
        plVar4 = (longlong *)FUN_14102a280(param_1);
        cVar2 = (**(code **)(*plVar4 + 0x180))(*plVar4,cVar6);
        if (cVar2 != '\0') {
          uVar5 = FUN_141028aa0(param_1,cVar6);
          uVar5 = FUN_141015bf0(uVar5);
          uVar3 = FUN_141028b00(param_1,cVar6,param_2);
          FUN_141011720(uVar5,uVar3);
        }
        cVar6 = cVar6 + '\x01';
      } while (cVar6 != '\x03');
      param_2 = param_2 + 1;
      iVar8 = iVar8 + -1;
    } while (iVar8 != 0);
  }
  return;
}


