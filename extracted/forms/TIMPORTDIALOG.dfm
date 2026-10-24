object ImportDialog: TImportDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgImport'
  BorderIcons = [biSystemMenu, biHelp]
  BorderStyle = bsSizeable
  Caption = 'Import Settings'
  ClientHeight = 298
  ClientWidth = 345
  Constraints.MinHeight = 190
  Constraints.MinWidth = 266
  OnClose = FormClose
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object BottomLineBevel: TUiBevel
    Left = 0
    Top = 257
    Width = 345
    Height = 2
    Align = alBottom
    Shape = bsBottomLine
  end
  object PanelView: TUiActivePanelView
    Left = 0
    Top = 0
    Width = 345
    Height = 257
    Align = alClient
    TabOrder = 0
    UsesAnchors = True
    object FilePanel: TUiActivePanel
      Width = 345
      Height = 257
      DesignSize = (345, 257)
      object FileLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Import Beyond Compare settings'
        FontStyle = [fsBold]
      end
      object FilenameLbl: TUiLabel
        Left = 8
        Top = 29
        Height = 13
        Caption = '&Select import file:'
        FocusControl = FilenameEdit
      end
      object FilenameEdit: TUiSpecBar
        Left = 8
        Top = 46
        Width = 329
        Anchors = [akLeft, akTop, akRight]
        TabOrder = 0
        OnBrowse = FilenameEditBrowse
        OnChange = SomethingChangedClick
      end
    end
    object AffectPanel: TUiActivePanel
      Width = 345
      Height = 257
      DesignSize = (345, 257)
      object AffectLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'What settings do you want to import?'
        FontStyle = [fsBold]
      end
      object AffectListBox: TUiCheckListBox
        Left = 8
        Top = 29
        Width = 329
        Height = 189
        OnClickCheck = SomethingChangedClick
        Anchors = [akLeft, akTop, akRight, akBottom]
        TabOrder = 0
        OnDrawItem = AffectListBoxDrawItem
      end
      object AffectAllBtn: TUiBitBtn
        Left = 8
        Top = 226
        Width = 24
        Hint = 'Mark All'
        Anchors = [akLeft, akBottom]
        ImageIndex = imgCheckAll
        Images = BcImages.MainImages
        TabOrder = 1
        OnClick = CheckedChangeClick
      end
      object AffectNoneBtn: TUiBitBtn
        Left = 32
        Top = 226
        Width = 24
        Hint = 'Unmark All'
        Anchors = [akLeft, akBottom]
        ImageIndex = imgUncheckAll
        Images = BcImages.MainImages
        TabOrder = 2
        OnClick = CheckedChangeClick
      end
    end
    object SessionsPanel: TUiActivePanel
      Width = 345
      Height = 257
      DesignSize = (345, 257)
      object SessionsLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Pick sessions to import:'
        FontStyle = [fsBold]
      end
      object SessionsListBox: TUiCheckListBox
        Left = 8
        Top = 29
        Width = 329
        Height = 164
        OnClickCheck = SomethingChangedClick
        Anchors = [akLeft, akTop, akRight, akBottom]
        TabOrder = 0
        OnDrawItem = SessionsListBoxDrawItem
        Images = BcImages.MainImages
        OnGetImageIndex = SessionsListBoxGetImageIndex
        OnGetNotLast = SessionsListBoxGetNotLast
        OnGetOverlayIndex = SessionsListBoxGetOverlayIndex
      end
      object SessionsAllBtn: TUiBitBtn
        Left = 8
        Top = 201
        Width = 24
        Hint = 'Mark All'
        Anchors = [akLeft, akBottom]
        ImageIndex = imgCheckAll
        Images = BcImages.MainImages
        TabOrder = 1
        OnClick = CheckedChangeClick
      end
      object SessionsNoneBtn: TUiBitBtn
        Left = 32
        Top = 201
        Width = 24
        Hint = 'Unmark All'
        Anchors = [akLeft, akBottom]
        ImageIndex = imgUncheckAll
        Images = BcImages.MainImages
        TabOrder = 2
        OnClick = CheckedChangeClick
      end
      object SessionsDeleteEdit: TUiCheckBox
        Left = 8
        Top = 232
        Height = 17
        Anchors = [akLeft, akBottom]
        Caption = '&Delete all existing sessions'
        TabOrder = 3
        OnClick = SomethingChangedClick
      end
    end
    object FileFormatsPanel: TUiActivePanel
      Width = 345
      Height = 257
      DesignSize = (345, 257)
      object FileFormatsLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Pick file formats to import:'
        FontStyle = [fsBold]
      end
      object FileFormatsListBox: TUiCheckListBox
        Left = 8
        Top = 29
        Width = 329
        Height = 164
        OnClickCheck = SomethingChangedClick
        Anchors = [akLeft, akTop, akRight, akBottom]
        TabOrder = 0
        OnDrawItem = FileFormatsListBoxDrawItem
        Images = BcImages.MainImages
        OnGetImageIndex = FileFormatsListBoxGetImageIndex
      end
      object FileFormatsAllBtn: TUiBitBtn
        Left = 8
        Top = 201
        Width = 24
        Hint = 'Mark All'
        Anchors = [akLeft, akBottom]
        ImageIndex = imgCheckAll
        Images = BcImages.MainImages
        TabOrder = 1
        OnClick = CheckedChangeClick
      end
      object FileFormatsNoneBtn: TUiBitBtn
        Left = 32
        Top = 201
        Width = 24
        Hint = 'Unmark All'
        Anchors = [akLeft, akBottom]
        ImageIndex = imgUncheckAll
        Images = BcImages.MainImages
        TabOrder = 2
        OnClick = CheckedChangeClick
      end
      object FileFormatsDeleteEdit: TUiCheckBox
        Left = 8
        Top = 232
        Height = 17
        Anchors = [akLeft, akBottom]
        Caption = '&Delete all existing file formats'
        TabOrder = 3
        OnClick = SomethingChangedClick
      end
    end
    object ProfilesPanel: TUiActivePanel
      Width = 345
      Height = 257
      DesignSize = (345, 257)
      object ProfilesLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Pick profiles to import:'
        FontStyle = [fsBold]
      end
      object ProfilesListBox: TUiCheckListBox
        Left = 8
        Top = 29
        Width = 329
        Height = 164
        OnClickCheck = SomethingChangedClick
        Anchors = [akLeft, akTop, akRight, akBottom]
        TabOrder = 0
        OnDrawItem = ProfilesListBoxDrawItem
        Images = BcImages.MainImages
        OnGetImageIndex = ProfilesListBoxGetImageIndex
        OnGetNotLast = ProfilesListBoxGetNotLast
      end
      object ProfilesAllBtn: TUiBitBtn
        Left = 8
        Top = 201
        Width = 24
        Hint = 'Mark All'
        Anchors = [akLeft, akBottom]
        ImageIndex = imgCheckAll
        Images = BcImages.MainImages
        TabOrder = 1
        OnClick = CheckedChangeClick
      end
      object ProfilesNoneBtn: TUiBitBtn
        Left = 32
        Top = 201
        Width = 24
        Hint = 'Unmark All'
        Anchors = [akLeft, akBottom]
        ImageIndex = imgUncheckAll
        Images = BcImages.MainImages
        TabOrder = 2
        OnClick = CheckedChangeClick
      end
      object ProfilesDeleteEdit: TUiCheckBox
        Left = 8
        Top = 232
        Height = 17
        Anchors = [akLeft, akBottom]
        Caption = '&Delete all existing FTP profiles'
        TabOrder = 3
        OnClick = SomethingChangedClick
      end
    end
    object ConfirmPanel: TUiActivePanel
      Width = 345
      Height = 257
      DesignSize = (345, 257)
      object ConfirmLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Confirm selection'
        FontStyle = [fsBold]
      end
      object ConfirmFinishLbl: TUiLabel
        Left = 8
        Top = 232
        Height = 13
        Anchors = [akLeft, akBottom]
        Caption = 'To begin the import, click Finish.'
      end
      object ConfirmListBox: TUiListBox
        Left = 8
        Top = 29
        Width = 329
        Height = 195
        Anchors = [akLeft, akTop, akRight, akBottom]
        TabOrder = 0
      end
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 259
    Width = 345
    TabOrder = 1
    SizeGripper = True
    object BackBtn: TUiBackBtn
      OnClick = BackClick
    end
    object NextBtn: TUiNextBtn
      OnClick = NextClick
    end
    object CancelBtn: TUiCancelBtn
    end
  end
end
