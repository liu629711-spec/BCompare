object VfsSVNProfileGeneralFrame: TVfsSVNProfileGeneralFrame
  HelpType = htKeyword
  HelpKeyword = 'ProfileSVN'
  Caption = 'General'
  object SpecPanel: TUiPanel
    Left = 0
    Top = 0
    Width = 255
    Height = 92
    Align = alTop
    BevelOuter = bvNone
    TabOrder = 0
    object URLLbl: TUiLabel
      Left = 8
      Top = 8
      Height = 13
      Caption = '&URL of repository:'
      FocusControl = URLEdit
    end
    object RevisionLbl: TUiLabel
      Left = 8
      Top = 54
      Height = 13
      Caption = '&Revision:'
      FocusControl = RevisionEdit
    end
    object URLEdit: TUiEdit
      Left = 8
      Top = 25
      Width = 239
      Height = 21
      TabOrder = 0
      OnChange = SomethingChangedClick
    end
    object RevisionEdit: TUiEdit
      Left = 8
      Top = 71
      Width = 239
      Height = 21
      TabOrder = 1
      OnChange = SomethingChangedClick
    end
  end
  object PanelView: TUiActivePanelView
    Left = 0
    Top = 92
    Width = 255
    Height = 217
    Align = alClient
    TabOrder = 1
    object DescriptionPanel: TUiActivePanel
      object DescriptionLbl: TUiLabel
        Left = 8
        Top = 8
        Height = 13
        Caption = 'D&escription:'
        FocusControl = DescriptionEdit
      end
      object DescriptionEdit: TUiMemo
        Left = 8
        Top = 25
        Width = 239
        Height = 184
        ScrollBars = ssVertical
        TabOrder = 0
        OnChange = SomethingChangedClick
      end
    end
    object BrowsePanel: TUiActivePanel
      object BrowseFrame: TProfileBrowseRemoteFrame
        Left = 8
        Top = 39
        Width = 239
        Height = 170
        TabOrder = 0
        object TreeView: TUiTreeView
          Width = 239
          Height = 170
        end
      end
      object BrowseBtn: TUiButton
        Left = 8
        Top = 8
        Caption = 'Connect && &Browse'
        TabOrder = 1
        OnClick = BrowseClick
        AutoSize = asLeft
      end
    end
  end
end
