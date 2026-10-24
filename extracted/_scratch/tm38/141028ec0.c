function: FUN_141028ec0
entry: 141028ec0
body_size: 1732
signature: undefined FUN_141028ec0()


undefined1 FUN_141028ec0(longlong param_1)

{
  char cVar1;
  longlong *plVar2;
  undefined8 uVar3;
  bool bVar4;
  undefined1 local_11;
  longlong local_10;
  
  local_10 = 0;
  plVar2 = (longlong *)FUN_14102a280(*(undefined8 *)(param_1 + 0x40));
  cVar1 = (**(code **)(*plVar2 + 0x180))(*plVar2,2);
  if (cVar1 != '\0') {
    uVar3 = FUN_14102a280(*(undefined8 *)(param_1 + 0x40));
    FUN_140e686b0(uVar3,&local_10,2);
    if (local_10 != 0) {
      cVar1 = FUN_14102a200(*(undefined8 *)(param_1 + 0x40),0,*(undefined4 *)(param_1 + 0x48));
      if (cVar1 == '\x01') {
        cVar1 = FUN_14102a200(*(undefined8 *)(param_1 + 0x40),1,*(undefined4 *)(param_1 + 0x48));
        if (cVar1 == '\x01') {
          cVar1 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),*(undefined4 *)(param_1 + 0x48));
          if (cVar1 != '\x01') {
            FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",
                          0x7f1);
          }
          local_11 = 0;
        }
        else {
          uVar3 = FUN_14102a200(*(undefined8 *)(param_1 + 0x40),1,*(undefined4 *)(param_1 + 0x48));
          if ((byte)uVar3 < 8) {
            bVar4 = ((byte)((int)CONCAT71((int7)((ulonglong)uVar3 >> 8),1) << ((byte)uVar3 & 0x1f))
                    & DAT_14102963c) != 0;
          }
          else {
            bVar4 = false;
          }
          if (bVar4) {
            uVar3 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),*(undefined4 *)(param_1 + 0x48));
            if ((byte)uVar3 < 8) {
              bVar4 = ((byte)((int)CONCAT71((int7)((ulonglong)uVar3 >> 8),1) << ((byte)uVar3 & 0x1f)
                             ) & DAT_14102963c) != 0;
            }
            else {
              bVar4 = false;
            }
            if (!bVar4) {
              FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas"
                            ,0x7f5);
            }
            local_11 = 6;
          }
          else {
            cVar1 = FUN_14102a200(*(undefined8 *)(param_1 + 0x40),1,*(undefined4 *)(param_1 + 0x48))
            ;
            if (cVar1 != '\x04') {
              FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas"
                            ,0x7f9);
            }
            cVar1 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),*(undefined4 *)(param_1 + 0x48));
            if (cVar1 != '\x04') {
              FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas"
                            ,0x7fa);
            }
            local_11 = 2;
          }
        }
      }
      else {
        uVar3 = FUN_14102a200(*(undefined8 *)(param_1 + 0x40),0,*(undefined4 *)(param_1 + 0x48));
        if ((byte)uVar3 < 8) {
          bVar4 = ((byte)((int)CONCAT71((int7)((ulonglong)uVar3 >> 8),1) << ((byte)uVar3 & 0x1f)) &
                  DAT_14102963c) != 0;
        }
        else {
          bVar4 = false;
        }
        if (bVar4) {
          cVar1 = FUN_14102a200(*(undefined8 *)(param_1 + 0x40),1,*(undefined4 *)(param_1 + 0x48));
          if (cVar1 == '\x01') {
            uVar3 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),*(undefined4 *)(param_1 + 0x48));
            if ((byte)uVar3 < 8) {
              bVar4 = ((byte)((int)CONCAT71((int7)((ulonglong)uVar3 >> 8),1) << ((byte)uVar3 & 0x1f)
                             ) & DAT_14102963c) != 0;
            }
            else {
              bVar4 = false;
            }
            if (!bVar4) {
              FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas"
                            ,0x7ff);
            }
            local_11 = 5;
          }
          else {
            uVar3 = FUN_14102a200(*(undefined8 *)(param_1 + 0x40),1,*(undefined4 *)(param_1 + 0x48))
            ;
            if ((byte)uVar3 < 8) {
              bVar4 = ((byte)((int)CONCAT71((int7)((ulonglong)uVar3 >> 8),1) << ((byte)uVar3 & 0x1f)
                             ) & DAT_14102963c) != 0;
            }
            else {
              bVar4 = false;
            }
            if (bVar4) {
              cVar1 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),*(undefined4 *)(param_1 + 0x48))
              ;
              if (cVar1 == '\x01') {
                local_11 = 8;
              }
              else {
                uVar3 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),
                                      *(undefined4 *)(param_1 + 0x48));
                if ((byte)uVar3 < 8) {
                  bVar4 = ((byte)((int)CONCAT71((int7)((ulonglong)uVar3 >> 8),1) <<
                                 ((byte)uVar3 & 0x1f)) & DAT_14102963c) != 0;
                }
                else {
                  bVar4 = false;
                }
                if (bVar4) {
                  local_11 = 7;
                }
                else {
                  cVar1 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),
                                        *(undefined4 *)(param_1 + 0x48));
                  if (cVar1 != '\x04') {
                    FUN_140013b60(L"Assertion failure",
                                  L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",0x808);
                  }
                  local_11 = 3;
                }
              }
            }
            else {
              cVar1 = FUN_14102a200(*(undefined8 *)(param_1 + 0x40),1,
                                    *(undefined4 *)(param_1 + 0x48));
              if (cVar1 != '\x04') {
                FUN_140013b60(L"Assertion failure",
                              L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",0x80c);
              }
              cVar1 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),*(undefined4 *)(param_1 + 0x48))
              ;
              if (cVar1 == '\x01') {
                FUN_140013b60(L"Assertion failure",
                              L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",0x80d);
              }
              local_11 = 10;
            }
          }
        }
        else {
          cVar1 = FUN_14102a200(*(undefined8 *)(param_1 + 0x40),0,*(undefined4 *)(param_1 + 0x48));
          if (cVar1 != '\x04') {
            FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",
                          0x811);
          }
          cVar1 = FUN_14102a200(*(undefined8 *)(param_1 + 0x40),1,*(undefined4 *)(param_1 + 0x48));
          if (cVar1 == '\x01') {
            cVar1 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),*(undefined4 *)(param_1 + 0x48));
            if (cVar1 != '\x04') {
              FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas"
                            ,0x813);
            }
            local_11 = 1;
          }
          else {
            uVar3 = FUN_14102a200(*(undefined8 *)(param_1 + 0x40),1,*(undefined4 *)(param_1 + 0x48))
            ;
            if ((byte)uVar3 < 8) {
              bVar4 = ((byte)((int)CONCAT71((int7)((ulonglong)uVar3 >> 8),1) << ((byte)uVar3 & 0x1f)
                             ) & DAT_14102963c) != 0;
            }
            else {
              bVar4 = false;
            }
            if (bVar4) {
              cVar1 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),*(undefined4 *)(param_1 + 0x48))
              ;
              if (cVar1 == '\x01') {
                FUN_140013b60(L"Assertion failure",
                              L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",0x817);
              }
              local_11 = 9;
            }
            else {
              cVar1 = FUN_14102a200(*(undefined8 *)(param_1 + 0x40),1,
                                    *(undefined4 *)(param_1 + 0x48));
              if (cVar1 != '\x04') {
                FUN_140013b60(L"Assertion failure",
                              L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",0x81b);
              }
              cVar1 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),*(undefined4 *)(param_1 + 0x48))
              ;
              if (cVar1 == '\x01') {
                local_11 = 0xb;
              }
              else {
                uVar3 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),
                                      *(undefined4 *)(param_1 + 0x48));
                if ((byte)uVar3 < 8) {
                  bVar4 = ((byte)((int)CONCAT71((int7)((ulonglong)uVar3 >> 8),1) <<
                                 ((byte)uVar3 & 0x1f)) & DAT_14102963c) != 0;
                }
                else {
                  bVar4 = false;
                }
                if (bVar4) {
                  local_11 = 0xc;
                }
                else {
                  cVar1 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),
                                        *(undefined4 *)(param_1 + 0x48));
                  if (cVar1 != '\x04') {
                    FUN_140013b60(L"Assertion failure",
                                  L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",0x821);
                  }
                  local_11 = 3;
                }
              }
            }
          }
        }
      }
      goto code_r0x000141029570;
    }
  }
  cVar1 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),*(undefined4 *)(param_1 + 0x48));
  if (cVar1 == '\x01') {
    local_11 = 0;
  }
  else {
    uVar3 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),*(undefined4 *)(param_1 + 0x48));
    if ((byte)uVar3 < 8) {
      bVar4 = ((byte)((int)CONCAT71((int7)((ulonglong)uVar3 >> 8),1) << ((byte)uVar3 & 0x1f)) &
              DAT_14102963c) != 0;
    }
    else {
      bVar4 = false;
    }
    if (bVar4) {
      cVar1 = FUN_141028e40(*(undefined8 *)(param_1 + 0x40),0,*(undefined4 *)(param_1 + 0x48));
      if (cVar1 == '\0') {
        cVar1 = FUN_141028e40(*(undefined8 *)(param_1 + 0x40),1,*(undefined4 *)(param_1 + 0x48));
        if (cVar1 == '\0') {
          local_11 = 7;
        }
        else {
          local_11 = 5;
        }
      }
      else {
        local_11 = 6;
      }
    }
    else {
      cVar1 = FUN_141028d90(*(undefined8 *)(param_1 + 0x40),*(undefined4 *)(param_1 + 0x48));
      if (cVar1 != '\x04') {
        FUN_140013b60(L"Assertion failure",L"C:\\BCBuild\\BCompare\\Source\\Text\\TextMap.pas",0x830
                     );
      }
      cVar1 = FUN_141028e40(*(undefined8 *)(param_1 + 0x40),0,*(undefined4 *)(param_1 + 0x48));
      if (cVar1 == '\0') {
        cVar1 = FUN_141028e40(*(undefined8 *)(param_1 + 0x40),1,*(undefined4 *)(param_1 + 0x48));
        if (cVar1 == '\0') {
          local_11 = 3;
        }
        else {
          local_11 = 1;
        }
      }
      else {
        local_11 = 2;
      }
    }
  }
code_r0x000141029570:
  FUN_140013e30(&local_10);
  return local_11;
}


