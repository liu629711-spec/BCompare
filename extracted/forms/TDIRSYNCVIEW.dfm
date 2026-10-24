object DirSyncView: TDirSyncView
  HelpType = htKeyword
  HelpKeyword = 'ViewDirSync'
  object TopPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 750
    Height = 175
    Align = alTop
    BevelOuter = bvNone
    TabOrder = 0
    object SwapBtn: TUiSpeedButton
      Left = 363
      Top = 8
      Hint = 'Swap Sides|Exchanges left, right base folders.'
      Flat = False
      ImageIndex = imgSwap
      Images = BcImages.MainImages
      OnClick = SwapExecute
    end
    object LeftArrowShape: TUiArrowShape
      Left = 2
      Top = 30
      Width = 24
      Height = 41
      ArrowHeads = ahNone
    end
    object PresetLbl: TUiLabel
      Left = 27
      Top = 37
      Height = 13
      Caption = 'Operations:'
    end
    object PresetDescLbl: TUiLabel
      Left = 27
      Top = 81
      Height = 13
      Caption = 'Update each side with newer, orphan files from other side'
    end
    object RulesBtn: TUiSpeedButton
      Left = 285
      Top = 54
      Hint = 'Rules|Edits current Rules definitions.'
      Flat = False
      ImageIndex = imgRules
      Images = BcImages.MainImages
      OnClick = RulesExecute
    end
    object CenterArrowShape: TUiArrowShape
      Left = 309
      Top = 54
      Width = 53
      Height = 21
      ArrowHeads = ahNone
      Direction = adRight
    end
    object NameFilterLbl: TUiLabel
      Left = 363
      Top = 37
      Height = 13
      Caption = 'Filters:'
    end
    object NameFilterBtn: TUiSpeedButton
      Left = 540
      Top = 54
      Hint = 'Name Filters|Edits name file filters.'
      Flat = False
      ImageIndex = imgFilters
      Images = BcImages.MainImages
      OnClick = NameFilterClick
    end
    object RightArrowShape: TUiArrowShape
      Left = 564
      Top = 30
      Width = 24
      Height = 41
      ArrowHeads = ahNone
      Direction = adRightUp
    end
    object RunStatsLbl: TUiLabel
      Left = 27
      Top = 102
      Width = 328
      Height = 65
      AutoSize = False
      Caption = '%'
    end
    object SummaryLbl: TUiLabel
      Left = 363
      Top = 83
      Width = 298
      Height = 13
      Caption = '%'
      WordWrap = True
    end
    object LeftSpecEdit: TUiSpecComboBar
      Left = 8
      Top = 8
      Width = 347
      AllowDropFiles = False
      AutoCompleteEx = acDirs
      EllipsisPosition = epPathEllipsis
      Images = BcImages.MainImages
      SupportsProfile = True
      TabOrder = 0
      OnAccept = AcceptClick
      OnBrowse = SpecEditBrowse
      OnChange = SpecEditChange
      OnDropDown = SpecEditDropDown
    end
    object RightSpecEdit: TUiSpecComboBar
      Left = 394
      Top = 8
      Width = 348
      AllowDropFiles = False
      AutoCompleteEx = acDirs
      EllipsisPosition = epPathEllipsis
      Images = BcImages.MainImages
      SupportsProfile = True
      TabOrder = 1
      OnAccept = AcceptClick
      OnBrowse = SpecEditBrowse
      OnChange = SpecEditChange
      OnDropDown = SpecEditDropDown
    end
    object PresetEdit: TUiComboBox
      Left = 27
      Top = 54
      Width = 250
      Height = 21
      Style = csDropDownList
      TabOrder = 2
      OnChange = PresetEditChange
      Images = BcImages.MainImages
      OnGetImageIndex = PresetEditGetImageIndex
    end
    object NameFilterEdit: TUiComboBox
      Left = 363
      Top = 54
      Width = 169
      Height = 21
      TabOrder = 3
    end
    object AcceptBtn: TUiBitBtn
      Left = 587
      Top = 54
      Width = 74
      Caption = 'Accept'
      ImageIndex = imgAccept
      Images = BcImages.MainImages
      TabOrder = 4
      OnClick = AcceptClick
      AutoSize = asRight
    end
    object CancelBtn: TUiBitBtn
      Left = 669
      Top = 54
      Caption = 'Cancel'
      ImageIndex = imgSyncCancel
      Images = BcImages.MainImages
      TabOrder = 5
      OnClick = CancelClick
      AutoSize = asRight
    end
    object RunBtn: TUiBitBtn
      Left = 669
      Top = 83
      Height = 57
      TabOrder = 6
      AutoSize = asLeft
      Layout = blImageBottom
    end
  end
  object MainPanel: TUiPanel
    Top = 175
    Height = 406
    TabOrder = 1
    object OtherFiltersPanel: TUiPanel
      Top = 383
    end
    object RunNoPanel: TUiPanel
      Left = 298
      Top = 34
      Width = 153
      Height = 41
      BorderStyle = bsSingle
      Caption = 'Nothing to sync!'
      Color = clWindow
      Ctl3D = False
      ParentBackground = False
      ParentCtl3D = False
      TabOrder = 1
    end
  end
  object MessagePanel: TUiPanel
    TabOrder = 2
  end
  object LogFrame: TLogFrame
    TabOrder = 3
    object ListBox: TUiVirtualListBox
      PopupMenu = LogPopup
    end
  end
end
