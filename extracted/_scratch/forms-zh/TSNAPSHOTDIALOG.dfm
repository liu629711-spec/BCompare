object SnapshotDialog: TSnapshotDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgSnapshot'
  BorderIcons = [biSystemMenu, biHelp]
  Caption = 'Save Snapshot'
  ClientHeight = 299
  ClientWidth = 393
  OnCloseQuery = FormCloseQuery
  OnCreate = FormCreate
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object PanelView: TUiActivePanelView
    Left = 0
    Top = 0
    Width = 393
    Height = 260
    TabOrder = 0
    object ConfirmPanel: TUiActivePanel
      object DirLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Fol&der:'
        FocusControl = DirEdit
      end
      object IncludeLbl: TUiLabel
        Left = 8
        Top = 117
        Height = 13
        Caption = 'Include:'
      end
      object DirUseLeftEdit: TUiRadioButton
        Left = 8
        Top = 25
        Height = 17
        Caption = '&Left base folder'
        TabOrder = 0
        OnClick = DirUseClick
      end
      object DirUseRightEdit: TUiRadioButton
        Left = 8
        Top = 46
        Height = 17
        Caption = '&Right base folder'
        TabOrder = 1
        OnClick = DirUseClick
      end
      object DirUseOtherEdit: TUiRadioButton
        Left = 8
        Top = 67
        Height = 17
        Caption = '&Other:'
        TabOrder = 2
        OnClick = DirUseClick
      end
      object DirEdit: TUiSpecBar
        Left = 24
        Top = 88
        Width = 361
        AutoCompleteEx = acDirs
        Images = BcImages.MainImages
        SupportsProfile = True
        TabOrder = 3
        OnBrowse = DirEditBrowse
        OnChange = DirEditChange
        OnUpdateTitles = DirEditUpdateTitles
      end
      object IncludeCRCsEdit: TUiCheckBox
        Left = 8
        Top = 138
        Height = 17
        Caption = '&CRCs'
        TabOrder = 4
      end
      object IncludeExeVersionsEdit: TUiCheckBox
        Left = 8
        Top = 159
        Height = 17
        Caption = 'Exe &versions'
        TabOrder = 5
      end
      object IncludeArchiveContentsEdit: TUiCheckBox
        Left = 8
        Top = 180
        Height = 17
        Caption = '&Archive contents'
        TabOrder = 6
      end
      object IncludeEmptyDirsEdit: TUiCheckBox
        Left = 8
        Top = 201
        Height = 17
        Caption = '&Empty folders'
        TabOrder = 7
      end
      object IncludeSymlinkTargetsEdit: TUiCheckBox
        Left = 8
        Top = 222
        Height = 17
        Caption = '&Symbolic link targets'
        TabOrder = 8
      end
      object IncludeFilteredEdit: TUiCheckBox
        Left = 8
        Top = 243
        Height = 17
        Caption = 'Items excluded by &file filters'
        TabOrder = 9
      end
    end
    object ProgressPanel: TUiActivePanel
      object ProgressLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Saving snapshot'
      end
      object ProgressBar: TUiProgressBar
        Left = 8
        Top = 25
        Width = 377
        Height = 17
        TabOrder = 0
      end
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 260
    Width = 393
    TabOrder = 1
    object OkBtn: TUiOkBtn
      OnClick = OkClick
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
