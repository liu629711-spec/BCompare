object ExportDialog: TExportDialog
  HelpType = htKeyword
  HelpKeyword = 'DlgExport'
  BorderIcons = [biSystemMenu, biHelp]
  BorderStyle = bsSizeable
  Caption = 'Export Settings'
  ClientHeight = 278
  ClientWidth = 345
  Constraints.MinHeight = 190
  Constraints.MinWidth = 266
  OnCreate = FormCreate
  OnDestroy = FormDestroy
  OnShow = FormShow
  PixelsPerInch = 96
  TextHeight = 13
  object BottomLineBevel: TUiBevel
    Left = 0
    Top = 237
    Width = 345
    Height = 2
    Align = alBottom
    Shape = bsBottomLine
  end
  object PanelView: TUiActivePanelView
    Left = 0
    Top = 0
    Width = 345
    Height = 237
    Align = alClient
    TabOrder = 0
    UsesAnchors = True
    object AffectPanel: TUiActivePanel
      Width = 345
      Height = 237
      DesignSize = (345, 237)
      object AffectLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'What settings do you want to export?'
        FontStyle = [fsBold]
      end
      object AffectListBox: TUiCheckListBox
        Left = 8
        Top = 29
        Width = 329
        Height = 169
        OnClickCheck = SomethingChangedClick
        Anchors = [akLeft, akTop, akRight, akBottom]
        TabOrder = 0
      end
      object AffectAllBtn: TUiBitBtn
        Left = 8
        Top = 206
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
        Top = 206
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
      Height = 237
      DesignSize = (345, 237)
      object SessionsLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Pick sessions to export:'
        FontStyle = [fsBold]
      end
      object SessionsListBox: TUiCheckListBox
        Left = 8
        Top = 29
        Width = 329
        Height = 169
        OnClickCheck = SomethingChangedClick
        Anchors = [akLeft, akTop, akRight, akBottom]
        TabOrder = 0
        Images = BcImages.MainImages
        OnGetImageIndex = SessionsListBoxGetImageIndex
        OnGetNotLast = SessionsListBoxGetNotLast
        OnGetOverlayIndex = SessionsListBoxGetOverlayIndex
      end
      object SessionsAllBtn: TUiBitBtn
        Left = 8
        Top = 206
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
        Top = 206
        Width = 24
        Hint = 'Unmark All'
        Anchors = [akLeft, akBottom]
        ImageIndex = imgUncheckAll
        Images = BcImages.MainImages
        TabOrder = 2
        OnClick = CheckedChangeClick
      end
    end
    object FileFormatsPanel: TUiActivePanel
      Width = 345
      Height = 237
      DesignSize = (345, 237)
      object FileFormatsLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Pick file formats to export:'
        FontStyle = [fsBold]
      end
      object FileFormatsListBox: TUiCheckListBox
        Left = 8
        Top = 29
        Width = 329
        Height = 169
        OnClickCheck = SomethingChangedClick
        Anchors = [akLeft, akTop, akRight, akBottom]
        TabOrder = 0
        Images = BcImages.MainImages
        OnGetImageIndex = FileFormatsListBoxGetImageIndex
      end
      object FileFormatsAllBtn: TUiBitBtn
        Left = 8
        Top = 206
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
        Top = 206
        Width = 24
        Hint = 'Unmark All'
        Anchors = [akLeft, akBottom]
        ImageIndex = imgUncheckAll
        Images = BcImages.MainImages
        TabOrder = 2
        OnClick = CheckedChangeClick
      end
    end
    object ProfilesPanel: TUiActivePanel
      Width = 345
      Height = 237
      DesignSize = (345, 237)
      object ProfilesLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'Pick profiles to export:'
        FontStyle = [fsBold]
      end
      object ProfilesListBox: TUiCheckListBox
        Left = 8
        Top = 29
        Width = 329
        Height = 144
        OnClickCheck = SomethingChangedClick
        Anchors = [akLeft, akTop, akRight, akBottom]
        TabOrder = 0
        Images = BcImages.MainImages
        OnGetImageIndex = ProfilesListBoxGetImageIndex
        OnGetNotLast = ProfilesListBoxGetNotLast
      end
      object ProfilesAllBtn: TUiBitBtn
        Left = 8
        Top = 181
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
        Top = 181
        Width = 24
        Hint = 'Unmark All'
        Anchors = [akLeft, akBottom]
        ImageIndex = imgUncheckAll
        Images = BcImages.MainImages
        TabOrder = 2
        OnClick = CheckedChangeClick
      end
      object ProfilesPasswordsEdit: TUiCheckBox
        Left = 8
        Top = 212
        Height = 17
        Anchors = [akLeft, akBottom]
        Caption = 'Include &passwords'
        TabOrder = 3
        OnClick = SomethingChangedClick
      end
    end
  end
  object BtnPanel: TUiBtnPanel
    Left = 0
    Top = 239
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
